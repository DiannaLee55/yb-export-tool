"""
腾讯元宝 - 指定分组全量对话导出
用法：python3 export_group.py [--max-retry N]
  --max-retry N  没找到新内容时最多滚动重试次数
                 推荐值公式：ceil(N / 10) + 1，N 为分组内对话总数
                 例：10条→2, 20条→3, 50条→6, 66条→8, 100条→11, 150条→16
                 （不传此参数则默认 10）
"""
import argparse
import asyncio
import os
import time

from playwright.async_api import async_playwright

# --- 配置 ---
USER_DATA_PATH = os.path.join(os.getcwd(), "browser_session")
EXPORT_FILENAME = f"元宝分组全量备份_{time.strftime('%m%d_%H%M')}.md"

# ----------------------------------------------------------------
# 滚动方案说明
# 当前使用【方案 A：JS 操作列表容器 scrollTop】，更健壮，不依赖窗口坐标。
# 若方案 A 失效（如页面改版导致选择器失效），可切换为【方案 B：鼠标坐标滚动】：
#   将下方 scroll_list_down() 函数体替换为：
#     await page.mouse.move(SCROLL_X, SCROLL_Y)
#     await page.mouse.wheel(0, 1000)
#     await page.keyboard.press("PageDown")
# 原坐标（经用户实测验证）：
#   SCROLL_X = 800
#   SCROLL_Y = 500
# ----------------------------------------------------------------
LIST_CONTAINER_SEL = ".yb-project-inner"   # 分组列表的滚动容器

SELECTORS = {
    "card": ".yb-project-chat-item",
    "title": ".yb-project-chat-item-title",
    "chat_container": ".agent-chat__list__content",
    "back_btn": ".agent-project-breadcrumb--link",
}


def parse_args():
    parser = argparse.ArgumentParser(description="腾讯元宝指定分组全量导出")
    parser.add_argument(
        "--max-retry",
        type=int,
        default=10,
        help="视口无新卡片时最多滚动重试次数（默认 10）",
    )
    return parser.parse_args()


async def run_backup(max_retry: int):
    print(f"\n{'='*50}")
    print(f"滚动重试上限: {max_retry} 次")
    print(f"输出文件: {EXPORT_FILENAME}")
    print(f"{'='*50}")

    async def scroll_list_down(page) -> None:
        """方案 A：通过 JS 操作分组列表容器向下滚动。
        若此选择器失效，参考文件顶部注释切换为方案 B（鼠标坐标滚动）。
        """
        await page.evaluate(f"""() => {{
            const el = document.querySelector('{LIST_CONTAINER_SEL}');
            if (el) {{
                el.scrollTop += 1000;
            }}
        }}""")
        await page.keyboard.press("PageDown")  # 双保险

    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_PATH,
            headless=False,
            args=["--start-maximized"],
        )
        page = context.pages[0] if context.pages else await context.new_page()
        await page.goto("https://yuanbao.tencent.com/")

        print("\n" + "=" * 50)
        print("💡 操作提示：")
        print("1. 在浏览器中进入你想备份的【分组】。")
        print("2. 只要卡片列表出来了即可。")
        print("=" * 50)
        input("👉 准备就绪后，请在终端按 [Enter] 开始...")

        processed_ids: set = set()
        retry_scroll_count = 0

        with open(EXPORT_FILENAME, "w", encoding="utf-8") as f:
            f.write(
                f"# 元宝分组备份\n导出时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            )

            while True:
                # 1. 扫描当前视口中的卡片
                cards = await page.query_selector_all(SELECTORS["card"])
                target_card = None
                current_title = ""
                current_id = ""

                for card in cards:
                    cid = await card.get_attribute("id")
                    if cid and cid not in processed_ids:
                        target_card = card
                        title_node = await card.query_selector(SELECTORS["title"])
                        current_title = (
                            (await title_node.inner_text()).strip()
                            if title_node
                            else "无标题"
                        )
                        current_id = cid
                        break

                # 2. 视口无新卡片 → 滚动重试
                if not target_card:
                    if retry_scroll_count < max_retry:
                        print(
                            f"⏳ 视口未见新会话，正在尝试向下深度滚动"
                            f" (第 {retry_scroll_count + 1}/{max_retry} 次)..."
                        )
                        await scroll_list_down(page)
                        await asyncio.sleep(2)
                        retry_scroll_count += 1
                        continue
                    else:
                        print("✅ 已尝试多次滚动未发现新内容，任务结束。")
                        break

                # 3. 找到新卡片，开始处理
                retry_scroll_count = 0
                processed_ids.add(current_id)
                print(f"🚀 [{len(processed_ids)}] 抓取中: {current_title}")

                try:
                    await target_card.scroll_into_view_if_needed()
                    await target_card.click(force=True, timeout=5000)
                    await asyncio.sleep(3)
                except Exception:
                    print("⚠️ 点击失效，可能是虚拟列表将其销毁，跳过...")
                    continue

                # 4. 向上回溯抓取全量聊天内容
                session_data: dict = {}
                chat_last_h = 0
                chat_no_change = 0

                while chat_no_change < 3:
                    msg_items = await page.query_selector_all(
                        ".agent-chat__list__item"
                    )
                    for msg in msg_items:
                        mid = await msg.get_attribute("data-conv-idx")
                        if mid and mid not in session_data:
                            spk = await msg.get_attribute("data-conv-speaker")
                            role = "### [我]" if spk == "human" else "### [元宝]"
                            thought_el = await msg.query_selector(
                                ".hyc-component-reasoner__think-content"
                            )
                            thought = ""
                            if thought_el:
                                thought_text = (
                                    await thought_el.inner_text()
                                ).strip().replace("\n", "\n> ")
                                thought = f"> **思考过程：**\n> {thought_text}\n\n"
                            txt_el = await msg.query_selector(
                                ".hyc-common-markdown"
                            ) or await msg.query_selector(
                                ".agent-chat__bubble__content"
                            )
                            txt = (await txt_el.inner_text()).strip() if txt_el else ""
                            if txt:
                                session_data[mid] = f"{role}\n\n{thought}{txt}"

                    chat_container_sel = SELECTORS["chat_container"]
                    await page.evaluate(
                        f"if(document.querySelector('{chat_container_sel}'))"
                        f" document.querySelector('{chat_container_sel}').scrollTop = 0"
                    )
                    await asyncio.sleep(1.5)
                    curr_h = await page.evaluate(
                        f"document.querySelector('{chat_container_sel}')?.scrollHeight || 0"
                    )
                    if curr_h == chat_last_h:
                        chat_no_change += 1
                    else:
                        chat_no_change = 0
                        chat_last_h = curr_h

                # 5. 写入文件
                f.write(f"\n## 会话: {current_title}\n" + "-" * 30 + "\n")
                for k in sorted(session_data.keys(), key=int):
                    f.write(session_data[k] + "\n\n---\n")
                f.flush()
                print(f"   ✅ 已抓取 {len(session_data)} 条消息")

                # 6. 返回列表
                back = await page.query_selector(SELECTORS["back_btn"])
                if back:
                    await back.click()
                    await asyncio.sleep(2)
                else:
                    print("🔙 找不到返回按钮，执行后退...")
                    await page.go_back()
                    await asyncio.sleep(3)

        print(f"\n✨ 导出完成！共处理 {len(processed_ids)} 条会话")
        print(f"📄 文件已保存: {EXPORT_FILENAME}")
        await context.close()


if __name__ == "__main__":
    args = parse_args()
    asyncio.run(run_backup(max_retry=args.max_retry))

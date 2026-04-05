"""
腾讯元宝 - 未分组对话全量导出
用法：python3 export_ungrouped.py
导出侧边栏 Chat 列表中所有未归入分组的对话（带 dt-cid 属性的条目）
"""
import asyncio
import os

from playwright.async_api import async_playwright

# --- 配置 ---
USER_DATA_PATH = os.path.join(os.getcwd(), "browser_session")
EXPORT_FILENAME = "yuanbao_full_content.md"


async def auto_export():
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_PATH,
            headless=False,
            slow_mo=500,
        )
        page = await context.new_page()
        page.set_default_timeout(0)

        await page.goto("https://yuanbao.tencent.com/")
        print("\n" + "=" * 50)
        print("请在浏览器中确认已登录，侧边栏能够看到『Chat』和『Group』列表。")
        await asyncio.to_thread(
            input, "一切就绪后，在此按 Enter 开始全量深度备份：\n" + "=" * 50 + "\n"
        )

        # 1. 展开侧边栏所有隐藏内容
        print("正在展开所有会话分组...")
        try:
            more_btn = await page.query_selector(".yb-project-list__trigger")
            if more_btn:
                await more_btn.click()
                await asyncio.sleep(1)
            projects = await page.query_selector_all(".yb-project-list__item")
            for proj in projects:
                await proj.click()
                await asyncio.sleep(0.5)
        except Exception:
            pass

        # 2. 滚动侧边栏以加载完整会话列表
        print("同步会话列表...")
        conv_selector = ".yb-recent-conv-list__item[dt-cid]"
        last_count = 0
        while True:
            await page.hover(".yb-recent-conv-list")
            await page.mouse.wheel(0, 5000)
            await asyncio.sleep(2)
            items = await page.query_selector_all(conv_selector)
            if len(items) == last_count:
                break
            last_count = len(items)
            print(f"已发现 {last_count} 个有效对话...")

        print(f"共找到 {last_count} 个对话，开始逐一抓取...")

        # 3. 循环进入对话并逐条抓取
        with open(EXPORT_FILENAME, "a", encoding="utf-8") as f:
            f.write("\n# 元宝全量深度备份\n")

            for i in range(last_count):
                all_convs = await page.query_selector_all(conv_selector)
                target = all_convs[i]

                title_el = await target.query_selector(
                    ".yb-recent-conv-list__item-name"
                )
                session_title = (
                    (await title_el.inner_text()).strip()
                    if title_el
                    else f"Session_{i}"
                )

                print(f"[{i + 1}/{last_count}] 正在抓取会话: {session_title}")

                try:
                    await target.click()
                    await asyncio.sleep(3)

                    session_data: dict = {}
                    no_change_count = 0
                    prev_scroll_height = 0

                    # 向上回溯加载全量消息
                    while no_change_count < 5:
                        items_on_page = await page.query_selector_all(
                            ".agent-chat__list__item"
                        )
                        for item in items_on_page:
                            idx = await item.get_attribute("data-conv-idx")
                            if idx and idx not in session_data:
                                speaker = await item.get_attribute("data-conv-speaker")
                                role = "### [我]" if speaker == "human" else "### [元宝]"
                                content = await item.inner_text()
                                if content.strip():
                                    session_data[idx] = f"{role}\n{content.strip()}"

                        await page.evaluate("""() => {
                            const scroller =
                                document.querySelector('.agent-chat__list__content') ||
                                document.querySelector('.agent-chat__list');
                            if (scroller) scroller.scrollTop = 0;
                        }""")
                        await asyncio.sleep(1.5)

                        curr_h = await page.evaluate(
                            "document.querySelector('.agent-chat__list__content')"
                            "?.scrollHeight || 0"
                        )
                        if curr_h == prev_scroll_height:
                            no_change_count += 1
                        else:
                            no_change_count = 0
                            prev_scroll_height = curr_h

                    # 按时间顺序写入本会话
                    f.write(
                        f"\n\n## 会话名称: {session_title}\n" + "=" * 60 + "\n"
                    )
                    for key in sorted(session_data.keys(), key=int):
                        f.write(session_data[key] + "\n\n---\n")
                    f.flush()
                    print(f"  ✅ 已抓取 {len(session_data)} 条记录")

                except Exception as e:
                    print(f"  ⚠️ 会话 [{session_title}] 抓取异常: {e}")

        print(f"\n🎉 全量备份完成！文件已保存: {EXPORT_FILENAME}")
        await context.close()


if __name__ == "__main__":
    asyncio.run(auto_export())

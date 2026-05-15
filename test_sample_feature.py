import pytest
import time
from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.webdriver.common.appiumby import AppiumBy

class TestAppFeature:
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        # 1. 设置 Appium Desired Capabilities
        options = UiAutomator2Options()
        options.platform_name = 'Android'
        options.automation_name = 'UiAutomator2'
        options.ignore_hidden_api_policy_error = True
        options.no_reset = True
        # 限制单次代理命令最长阻塞 20 秒，避免整条脚本“卡死”
        options.set_capability('appium:uiautomator2ServerReadTimeout', 20000)

        # 2. 连接到本地 Appium Server
        self.driver = webdriver.Remote('http://127.0.0.1:4723', options=options)
        self.driver.implicitly_wait(1)
        
        yield  # 执行测试用例
        
        # 3. 测试结束，清理环境
        if self.driver:
            self.driver.quit()

    def test_multi_apps_launch(self):
        """循环测试多个分身应用的启动和稳定性"""
        apps_to_test = ["创业天下", "中国移动", "京东", "蚁丛旅游", "起点读书", "派派", "苏宁易购", "游吧通", "心遇"]
        step_timeout_sec = 20
        reports = []

        def swipe_up_once():
            """在结果列表或详情页中轻微上滑一次，帮助加载/暴露下方元素。"""
            size = self.driver.get_window_size()
            x = int(size["width"] * 0.5)
            start_y = int(size["height"] * 0.78)
            end_y = int(size["height"] * 0.40)
            self.driver.swipe(x, start_y, x, end_y, 350)

        def find_first(candidates, retries=2):
            """按候选定位依次查找元素，失败时短重试，避免卡住太久。"""
            for _ in range(retries):
                for by, value in candidates:
                    elems = self.driver.find_elements(by, value)
                    if elems:
                        return elems[0]
                time.sleep(0.8)
            return None

        def run_step(step_name, fn):
            """执行单步并统计耗时，超过 20 秒则视为阻塞并跳过当前应用。"""
            start = time.monotonic()
            result = fn()
            elapsed = time.monotonic() - start
            if elapsed > step_timeout_sec:
                raise Exception(f"{step_name} 阻塞超过 {step_timeout_sec} 秒")
            return result

        def click_search_result(app_name):
            """多轮查找并点击搜索结果，避免误点输入框。"""
            result_xpath = (
                f"//*[contains(@text, '{app_name}') and "
                "not(contains(@resource-id, 'etKey_search')) and "
                "not(contains(@class, 'EditText'))]"
            )
            for attempt in range(4):
                candidates = self.driver.find_elements(AppiumBy.XPATH, result_xpath)
                for item in candidates:
                    try:
                        res_id = str(item.get_attribute("resource-id"))
                        class_name = str(item.get_attribute("class"))
                        if "etKey_search" in res_id or "EditText" in class_name:
                            continue
                        item.click()
                        return True
                    except Exception:
                        continue
                if attempt < 3:
                    swipe_up_once()
                    time.sleep(1)
            return False

        def click_open_clone():
            """使用多种定位策略点击“打开分身”按钮。"""
            open_clone_xpaths = [
                "//*[@resource-id='info.red.virtual:id/tv_open_clone']",
                "//*[@resource-id='info.red.virtual:id/btn_open_clone']",
                "//*[@content-desc='打开分身' or @text='打开分身' or contains(@text, '打开分身')]",
                "//*[contains(@text, '打开分身')]/ancestor::*[@clickable='true'][1]",
            ]
            for attempt in range(4):
                for xpath in open_clone_xpaths:
                    elems = self.driver.find_elements(AppiumBy.XPATH, xpath)
                    for elem in elems:
                        try:
                            elem.click()
                            return True
                        except Exception:
                            continue
                if attempt < 3:
                    swipe_up_once()
                    time.sleep(1)
            return False
        
        for app_name in apps_to_test:
            print(f"\n\n{'='*40}")
            print(f"开始测试应用: {app_name}")
            print(f"{'='*40}")
            
            try:
                # 每次测试前，先强制停止宿主应用，确保从干净的首页面开始
                run_step("终止宿主应用", lambda: self.driver.terminate_app('info.red.virtual'))
                time.sleep(2)
                
                # 1. 启动目标应用
                print(f"---> 正在启动宿主应用 (悟空分身)...")
                run_step("启动宿主应用", lambda: self.driver.activate_app('info.red.virtual'))
                time.sleep(8) # 等待首页完全加载出来
                
                # 2. 定位并点击搜索入口 (放大镜)
                search_icon_id = "info.red.virtual:id/menu_item_search" 
                print(f"---> 准备点击搜索入口...")
                search_icon = run_step(
                    "查找搜索入口",
                    lambda: find_first([
                        (AppiumBy.ID, search_icon_id),
                        (AppiumBy.XPATH, "//android.widget.Button[@content-desc='搜索']"),
                        (AppiumBy.XPATH, "//*[contains(@content-desc,'搜索')]"),
                    ], retries=3),
                )
                if not search_icon:
                    raise Exception("未找到搜索入口，可能页面未加载完成或被弹窗遮挡")
                run_step("点击搜索入口", lambda: search_icon.click())
                time.sleep(2)
                
                # 3. 定位输入框并输入文字
                search_input_xpath = "//android.widget.EditText[@resource-id='info.red.virtual:id/etKey_search']" 
                print(f"---> 输入搜索内容: {app_name}")
                search_input = run_step(
                    "查找搜索输入框",
                    lambda: find_first([
                        (AppiumBy.XPATH, search_input_xpath),
                        (AppiumBy.XPATH, "//android.widget.EditText"),
                    ], retries=3),
                )
                if not search_input:
                    raise Exception("未找到搜索输入框")
                run_step("点击搜索输入框", lambda: search_input.click())
                time.sleep(1)
                run_step("输入搜索词", lambda: search_input.send_keys(app_name))
                
                # 4. 回车搜索
                print(f"---> 模拟按下键盘的回车键(搜索键)...")
                run_step("按回车搜索", lambda: self.driver.press_keycode(66))
                time.sleep(3)
                
                # 5. 点击搜索结果
                print(f"---> 准备点击搜索结果...")
                if not run_step("点击搜索结果", lambda: click_search_result(app_name)):
                    raise Exception(f"未找到可点击的 {app_name} 搜索结果")
                
                # 6. 等待详情页加载并点击“打开分身”按钮
                print(f"---> 准备点击打开分身按钮...")
                time.sleep(3)
                if not run_step("点击打开分身", lambda: click_open_clone()):
                    raise Exception(f'未找到 "{app_name}" 的打开分身按钮')
                
                # 7. 停留并监控20秒
                print(f"---> 成功点击打开分身！开始监控 20 秒...")
                
                crash_detected = False
                error_msg = ""
                
                # 每秒钟检查一次应用状态，持续20次
                for i in range(20):
                    time.sleep(1)
                    
                    try:
                        # 临时将隐式等待设置为 0，为了快速检查元素是否存在而不阻塞脚本
                        self.driver.implicitly_wait(0)
                        
                        # 检查1：是否弹出了系统的“停止运行/无响应”提示框
                        crash_dialogs = self.driver.find_elements(AppiumBy.XPATH, "//*[contains(@text, '停止运行') or contains(@text, '无响应') or contains(@text, '屡次停止运行')]")
                        if len(crash_dialogs) > 0:
                            crash_detected = True
                            error_msg = "弹出系统崩溃/无响应提示"
                            break
                            
                        # 检查2：是否闪退回到了“打开分身”的详情页
                        open_btns = self.driver.find_elements(AppiumBy.XPATH, "//*[contains(@text, '打开分身')]")
                        if len(open_btns) > 0:
                            crash_detected = True
                            error_msg = "闪退回到了分身详情页"
                            break
                            
                        # 检查3：是否闪退回到了宿主首页 (能看到搜索放大镜)
                        search_icons = self.driver.find_elements(AppiumBy.ID, search_icon_id)
                        if len(search_icons) > 0:
                            crash_detected = True
                            error_msg = "闪退回到了宿主首页"
                            break
                            
                    except Exception as inner_e:
                        pass
                    finally:
                        # 恢复默认的隐式等待，以免影响后续正常操作
                        self.driver.implicitly_wait(10)
                        
                if crash_detected:
                    msg = f'"{app_name}" 应用出现 {error_msg} 问题'
                    print(f'\n [失败] {msg}')
                    reports.append(f"[失败] {msg}")
                else:
                    msg = f'"{app_name}" 应用启动后 20 秒内运行正常，未发现闪退'
                    print(f'\n [成功] {msg}')
                    reports.append(f"[成功] {msg}")
                    
            except Exception as e:
                msg = f'"{app_name}" 应用在自动化操作过程中出现异常: {e}'
                print(f'\n [异常] {msg}')
                reports.append(f"[异常] {msg}")

        print("\n\n================ 测试汇总 ================")
        for item in reports:
            print(item)

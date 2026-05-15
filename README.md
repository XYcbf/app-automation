# App Automation（悟空分身稳定性巡检）

基于 **Appium + Python + pytest** 的 Android 真机自动化项目，用于在宿主应用 **悟空分身**（`info.red.virtual`）内批量执行：**搜索目标应用 → 进入详情页 → 点击“打开分身” → 运行 20 秒稳定性监控 → 汇总结果**。  
适用于回归测试与基础稳定性巡检（闪退/无响应/回退等问题的快速发现与记录）。

## 主要功能

- **批量应用巡检**：按配置列表依次搜索并打开分身（当前默认 9 个应用，可自行增减）。
- **统一业务链路**：搜索入口 → 输入关键字 → 回车搜索 → 点击结果 → 点击“打开分身”。
- **稳定性监控（20 秒）**：在分身启动后持续观察 20 秒，捕捉异常并输出报告。
- **超时保护与不中断执行**：单步骤超过 20 秒视为阻塞，自动跳过当前应用继续下一个，避免整条用例卡死。
- **鲁棒定位策略**：关键按钮使用 ID + 多 XPath 兜底；搜索结果点击避免误点搜索输入框。
- **统一输出格式**：以 `[成功] / [失败] / [异常]` 输出每个应用的执行结论，并在末尾打印汇总。

## 技术方法

- **自动化引擎**：Appium（UiAutomator2）驱动 Android 真机。
- **用例框架**：pytest（单脚本即可运行）。
- **定位策略**：
  - 优先使用稳定 `resource-id`（例如搜索入口 `info.red.virtual:id/menu_item_search`）。
  - 对动态页面使用 XPath `contains()` 做文本/属性模糊匹配。
  - 搜索结果采用“找全量元素 → 过滤输入框 → 点击可点击节点”的方式减少误点。
- **稳定性与可用性增强**：
  - 将 UiAutomator2 代理命令超时限制在 20 秒，降低“设备卡顿导致无限等待”的概率。
  - 为关键步骤增加单步耗时守卫，超时直接进入异常报告并跳过当前应用。

## 环境准备

### 1) 安装依赖

- Windows / macOS / Linux 均可
- Node.js（用于安装 Appium）
- Python 3（用于运行 pytest 脚本）
- Android SDK（需要 `adb` 可用）

安装 Appium 与驱动：

```bash
npm i -g appium
appium driver install uiautomator2
```

安装 Python 依赖（建议使用虚拟环境）：

```bash
pip install -U pytest Appium-Python-Client
```

### 2) 真机设置（必做）

- 开启开发者选项与 USB 调试
- 开启 USB 安装 / USB 调试（安全设置）/ 禁止权限监控（不同机型命名不同）
- 运行时保持手机 **解锁亮屏**，安装/风险弹窗务必点击 **允许/继续安装**

### 3) 启动 Appium Server

推荐（浏览器/Inspector 场景需要 CORS）：

```bash
appium --allow-cors
```

## 如何运行

在项目目录执行：

```bash
pytest -s test_sample_feature.py
```

运行过程中会在终端输出每个应用的过程与结果，末尾有“测试汇总”。

## 配置说明

核心配置在 [test_sample_feature.py](file:///d:/appAutomation/test_sample_feature.py)：

- 宿主包名：`info.red.virtual`
- 待测应用列表：`apps_to_test = [...]`
- 单步超时：`step_timeout_sec = 20`
- 稳定性监控时长：当前默认 20 秒（脚本内监控循环）

如果你需要新增/删除应用，只需改 `apps_to_test` 列表即可。

## 输出示例

```text
[成功] "京东" 应用启动后 20 秒内运行正常，未发现闪退
[失败] "蚁丛旅游" 应用出现 系统弹窗:停止运行 问题
[异常] "中国移动" 应用在自动化操作过程中出现异常: 未找到可点击的 中国移动 搜索结果

================ 测试汇总 ================
[成功] ...
[失败] ...
[异常] ...
```

## 常见问题排查

- **卡在安装 uiautomator2**：手机弹窗被覆盖/未点允许会导致 `INSTALL_FAILED_ABORTED`，保持亮屏并放行全部安装授权。
- **找不到元素**：页面加载慢/文案变化/列表异步刷新会导致定位失败，建议提高等待时间或在 Inspector 中重新确认定位信息。
- **执行中途卡死**：多为设备卡顿或 UiAutomator2 进程异常，本项目已增加单步 20 秒超时保护，会自动跳过并记录问题。

## 目录结构

- [test_sample_feature.py](file:///d:/appAutomation/test_sample_feature.py)：主测试脚本（包含业务链路与稳定性监控）
- [.gitignore](file:///d:/appAutomation/.gitignore)：忽略缓存与本地环境文件

## Roadmap（可选）

- 结果持久化（JSON/HTML 报告）
- 针对个别应用的“别名关键词”策略（例如同名/简称）
- 自动截图/录屏用于异常回放

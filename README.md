# Soundboard-WebView (音效播放器)

一款基于 **Android WebView + Web Audio API** 的音效播放器。原生壳加载本地 `index.html`，提供低延迟音效播放、分类管理、批量导入和持久化存储。

## 核心逻辑

- **UI 层**：`assets/index.html` 全部前端逻辑（原生 JS，无框架）。
- **播放层**：优先走 Web Audio API 解码缓冲播放，内置音效预解码并缓存到内存；Web Audio 不可用时回退到 `<audio>` 元素，并带对象池降低连按延迟。
- **存储层**：
  - 用户导入的音频二进制存入 **IndexedDB**；
  - 分类、自定义等配置存入 **LocalStorage**（支持旧版本配置自动迁移）。
- **内置音效**：按分类（如电棍、咕咕嘎嘎、大狗、无畏契约、终末地等）打包在 `assets/audio/`，清单写死在 `index.html`。
- **构建**：无 Gradle，纯脚本 `build_apk.py` 用 SDK 工具链（aapt / javac / d8 / zipalign / apksigner）直接打包 APK；`sync_audio_assets.py` 把源头文件夹的音效同步进 assets 并重写 `index.html` 清单。

## 使用方法

### 直接安装
- 下载 [Releases](https://github.com/xuan12345678900/Soundboard-WebView/releases) 里的 `Soundboard-WebView.apk` 安装到 Android 5.0+ 设备。

### 从源码构建 APK
1. 安装 Android SDK（build-tools 35.0.0）与 JDK 21；
2. 按需在 `sync_audio_assets.py` 里调整源头音频目录，运行它同步音效；
3. 运行 `python build_apk.py`，生成 `音效播放器.apk`。

## 功能清单

- 内置分类与音效一键播放（支持连按/叠放）
- 搜索音效
- 导入本地音频（批量、选择目标分类、自动过滤非音频）
- 新建 / 重命名 / 删除分类
- 播放中停止全部（红色按钮）
- 低延迟优化：音频模式为音乐流、预解码缓存、对象池复用
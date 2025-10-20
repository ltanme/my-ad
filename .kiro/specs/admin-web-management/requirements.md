# 需求文档

## 简介

本文档定义了媒体展示系统的Web管理后台功能需求。该管理后台是一个独立部署的Flask应用，用于管理media_display.db数据库中的媒体资源、播放列表和区域配置。管理后台采用前后端分离架构，使用Bootstrap 5.3.6和jQuery 3.7.1构建用户界面。

## 术语表

- **Admin_System**: 基于Flask的Web管理后台应用
- **Media_Database**: SQLite数据库文件(media_display.db)，存储媒体资源和播放列表信息
- **Zone**: 显示区域，系统预定义的9个媒体展示区域
- **Playlist**: 播放列表，包含多个媒体项的有序集合
- **Media_Asset**: 媒体资源，包括文本、图片或视频
- **Config_File**: YAML配置文件(config.yaml)，包含数据库路径、管理员凭证和媒体目录配置
- **User_Session**: 用户登录会话，用于验证管理员身份
- **Upload_Directory**: 媒体文件上传目标目录，在Config_File中配置

## 需求

### 需求 1: 用户认证

**用户故事:** 作为系统管理员，我希望通过用户名和密码登录管理后台，以便安全地管理媒体内容

#### 验收标准

1. WHEN 管理员访问Admin_System根路径，THE Admin_System SHALL 显示登录页面
2. WHEN 管理员提交有效的用户名和密码，THE Admin_System SHALL 创建User_Session并重定向到内容管理页面
3. WHEN 管理员提交无效的凭证，THE Admin_System SHALL 显示错误消息并保持在登录页面
4. WHEN 未认证用户尝试访问内容管理页面，THE Admin_System SHALL 重定向到登录页面
5. THE Admin_System SHALL 从Config_File读取管理员用户名和密码配置

### 需求 2: 配置文件管理

**用户故事:** 作为系统管理员，我希望通过配置文件管理系统设置，以便灵活配置数据库路径、认证信息和媒体目录

#### 验收标准

1. THE Admin_System SHALL 读取Config_File中的数据库文件路径配置
2. THE Admin_System SHALL 读取Config_File中的管理员用户名和密码配置
3. THE Admin_System SHALL 读取Config_File中的Upload_Directory路径配置
4. WHEN Config_File不存在或格式错误，THE Admin_System SHALL 记录错误并使用默认配置值
5. THE Admin_System SHALL 在启动时验证Media_Database文件路径的可访问性

### 需求 3: 区域展示和选择

**用户故事:** 作为系统管理员，我希望看到所有显示区域的布局，以便选择要管理的区域

#### 验收标准

1. THE Admin_System SHALL 在内容管理页面显示9个Zone的可视化布局
2. THE Admin_System SHALL 按照viewer模块的布局结构排列Zone显示
3. WHEN 管理员点击某个Zone，THE Admin_System SHALL 显示该Zone的播放列表管理界面
4. THE Admin_System SHALL 为每个Zone显示其名称和代码标识
5. THE Admin_System SHALL 在页面中心显示内容，左右各保留100像素边距

### 需求 4: 播放列表管理

**用户故事:** 作为系统管理员，我希望查看和管理每个区域的播放列表，以便组织媒体内容的播放顺序

#### 验收标准

1. WHEN 管理员选择某个Zone，THE Admin_System SHALL 显示该Zone的所有Playlist
2. THE Admin_System SHALL 为每个Playlist显示名称、激活状态和循环模式
3. WHEN 管理员点击创建播放列表按钮，THE Admin_System SHALL 显示创建Playlist的模态对话框
4. WHEN 管理员提交新Playlist信息，THE Admin_System SHALL 在Media_Database中创建Playlist记录
5. WHEN 管理员点击删除Playlist按钮，THE Admin_System SHALL 显示确认对话框并删除选中的Playlist
6. WHEN 管理员修改Playlist的激活状态，THE Admin_System SHALL 更新Media_Database中的is_active字段
7. THE Admin_System SHALL 确保每个Zone至多有一个激活的Playlist

### 需求 5: 媒体资源上传

**用户故事:** 作为系统管理员，我希望上传图片和视频文件，以便在播放列表中使用这些媒体资源

#### 验收标准

1. WHEN 管理员在Playlist管理界面点击上传按钮，THE Admin_System SHALL 显示文件选择对话框
2. THE Admin_System SHALL 接受图片文件格式(jpg, jpeg, png, gif, bmp)
3. THE Admin_System SHALL 接受视频文件格式(mp4, avi, mov, mkv, webm)
4. WHEN 管理员选择有效的媒体文件，THE Admin_System SHALL 将文件保存到Upload_Directory
5. WHEN 文件上传成功，THE Admin_System SHALL 在Media_Database的media_asset表中创建记录
6. WHEN 文件上传失败，THE Admin_System SHALL 显示错误消息并保留用户在页面上的操作状态
7. THE Admin_System SHALL 为上传的文件生成唯一文件名以避免冲突
8. THE Admin_System SHALL 在media_asset记录中存储文件的宽度、高度和时长信息

### 需求 6: 播放列表项管理

**用户故事:** 作为系统管理员，我希望在播放列表中添加、删除和排序媒体项，以便控制内容的播放顺序和参数

#### 验收标准

1. WHEN 管理员选择某个Playlist，THE Admin_System SHALL 显示该Playlist的所有播放项
2. WHEN 管理员点击添加媒体按钮，THE Admin_System SHALL 显示可用Media_Asset列表的模态对话框
3. WHEN 管理员选择Media_Asset并提交，THE Admin_System SHALL 在playlist_item表中创建记录
4. THE Admin_System SHALL 允许管理员为播放项设置display_ms、per_item_loops、scale_mode和volume参数
5. WHEN 管理员点击删除播放项按钮，THE Admin_System SHALL 从playlist_item表中删除该记录
6. THE Admin_System SHALL 提供拖拽功能以调整播放项的play_order顺序
7. WHEN 管理员修改播放项顺序，THE Admin_System SHALL 更新所有受影响项的play_order值

### 需求 7: 文本内容管理

**用户故事:** 作为系统管理员，我希望直接添加文本内容到播放列表，以便在跑马灯等区域显示文字信息

#### 验收标准

1. WHEN 管理员在Playlist中点击添加文本按钮，THE Admin_System SHALL 显示文本输入模态对话框
2. WHEN 管理员提交文本内容，THE Admin_System SHALL 在playlist_item表中创建text_inline记录
3. THE Admin_System SHALL 确保text_inline和asset_id字段互斥(只能有一个非空)
4. THE Admin_System SHALL 允许管理员编辑已存在的文本内容
5. WHEN 管理员删除文本播放项，THE Admin_System SHALL 从playlist_item表中删除该记录

### 需求 8: 响应式API设计

**用户故事:** 作为前端开发者，我希望使用RESTful API与后端交互，以便实现前后端分离的架构

#### 验收标准

1. THE Admin_System SHALL 提供POST /api/login接口用于用户认证
2. THE Admin_System SHALL 提供GET /api/zones接口返回所有Zone信息
3. THE Admin_System SHALL 提供GET /api/playlists/<zone_id>接口返回指定Zone的Playlist列表
4. THE Admin_System SHALL 提供POST /api/playlists接口创建新Playlist
5. THE Admin_System SHALL 提供DELETE /api/playlists/<playlist_id>接口删除Playlist
6. THE Admin_System SHALL 提供POST /api/upload接口处理媒体文件上传
7. THE Admin_System SHALL 提供GET /api/playlist-items/<playlist_id>接口返回播放项列表
8. THE Admin_System SHALL 提供POST /api/playlist-items接口添加播放项
9. THE Admin_System SHALL 提供DELETE /api/playlist-items/<item_id>接口删除播放项
10. THE Admin_System SHALL 提供PUT /api/playlist-items/reorder接口更新播放项顺序
11. THE Admin_System SHALL 为所有API响应返回JSON格式数据
12. WHEN API请求失败，THE Admin_System SHALL 返回适当的HTTP状态码和错误消息

### 需求 9: 用户界面布局

**用户故事:** 作为系统管理员，我希望使用清晰直观的界面，以便高效地管理媒体内容

#### 验收标准

1. THE Admin_System SHALL 使用Bootstrap 5.3.6框架构建响应式界面
2. THE Admin_System SHALL 在页面中心显示内容区域，左右各保留100像素边距
3. THE Admin_System SHALL 使用模态对话框进行数据编辑操作
4. THE Admin_System SHALL 在Zone布局中使用与viewer模块相同的区域排列方式
5. THE Admin_System SHALL 为每个操作提供视觉反馈(加载状态、成功提示、错误提示)
6. THE Admin_System SHALL 使用jQuery 3.7.1处理前端交互逻辑
7. THE Admin_System SHALL 将所有HTML模板存储在admin/template目录
8. THE Admin_System SHALL 将所有静态资源(CSS、JS)存储在admin/static目录

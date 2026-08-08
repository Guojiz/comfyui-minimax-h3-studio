# MiniMax H3 模型 - 使用手册

> 官方《MiniMax H3 模型 - 使用手册》原文（飞书文档导出，仅清理头部推广信息，正文未改动）。


---

# **MiniMax H3：开放通用的多模态智能**


# 一、模型定位

MiniMax H3 是新一代开放通用多模态视频模型，我们正在探索从“特化任务模型”迈向“通用多模态智能”的新范式。

H3 不再以图片、视频、声音的生成、编辑、参考等**单一任务**为边界，而是面向**由文本、图像、视频与声音共同构成的多模态上下文**，统一理解创作意图，完成更加自然、连贯的生成与表达。

**H3，迈向更通用的多模态智能。**



# 二、模型功能信息

|**核心维度**|**MiniMax\-H3**|
|---|---|
|**模型**|MiniMax\-H3|
|**输出时长**|4\-15秒|
|**输出宽高比**|首/尾帧模式下，遵循用户输入图片的原始长宽比<br>文生视频模式下，遵循用户指定21:9、16:9、4:3、1:1、3:4、9:16范围内的长宽比<br>全能参考模式下，遵循用户指定21:9、16:9、4:3、1:1、3:4、9:16范围内的长宽比或者选择自动模式由H3自行判断输出宽高比|
|**分辨率**|768p模式（已开放）<br>- 当输出宽高比在16:9\~9:16之间时，输出为短边768像素；否则输出分辨率总面积约为1M像素，例如21:9时宽高为1536×672<br>- 768p生成的结果可以升级至1440p<br>1440p模式**（官方推荐版👍）**<br>- 当输出宽高比在16:9\~9:16之间时，输出为短边1440像素；否则输出分辨率总面积约为3\.7M像素，例如21:9时宽高为2976×1248|
|**输出帧率**|24 FPS|
|**输出声音**|所有结果全部带声音输出，原生双声道|
|**输入条件**||
|**首/尾帧入口**|- 图片：0、1、2张；宽高范围 \[256, 5760\]；宽高比5:2\~2:5范围内<br>- 无图片输入时为文生视频模式|
|**全能参考入口**|- 图片： ≤ 9 张；宽高范围：\[256, 5760\]<br>- 视频 ：≤ 3 段；单段时长\[2, 15\]秒；总时长≤ 15秒；宽高范围：\[256, 5760\]；宽高比： 5:2\~2:5范围内<br>- 音频 ：≤ 3段，且必须配图片或视频输入，不能单独输入；单段时长：\[2, 15\]秒；总时长≤ 15秒<br>- 混合输入的总上限是 12 个文件<br>- 无图片、视频、音频输入时为文生视频模式|
|**输入格式支持**|视频：H\.264/AVC、H\.265/HEVC；视频内音频：AAC、MP3<br>图片：JPG、JPEG、PNG、WEBP、HEIC、HEIF<br>音频：WAV、MP3|
|**传入大小限制**|视频单个50MB；图片单个30MB；音频单个15MB（加起来的不限制，限制都在单个素材上）；API 请求体 64MB（推荐使用url传入素材）|
|**提示词字数上限**|不超过7000字符|
|**语言支持与本地化表达**|支持多语言提示词输入与输出<br>TTS （文本转语音）精准覆盖** 11 种语言**，包括中文、英语、日语、韩语、法语、德语、西班牙语等<br>更多语言可衍生探索，如阿拉伯语、泰语、印尼语、印地语等**40多种语言**<br>适合海外品牌传播、多语种广告、跨语言短片和本地化产品介绍等场景|



# 三、模型亮点能力\& 示例



|**三大能力**|**阐释**|
|---|---|
|<br>**原生多模态理解与生成**<br>|支持文字、图片、音频、视频等多种输入，理解不同素材中的人物、动作、声音、情绪、镜头、风格与表达意图，并将多种参考信息自然融合，完成从素材理解到完整视听内容生成的一体化创作。|
|**多模态精准编辑与控制**|支持对人物、物体、场景、声音与节奏进行多维度编辑，并具备精细化指令遵循能力。创作者可以在已有内容基础上持续修改和迭代，更准确地落实对画面、声音与内容细节的调整需求。|
|<br>**商用级多场景内容生成**<br>|面向影视、广告、品牌、电商与游戏等真实商业内容场景。它兼顾文字字幕、品牌信息、创意特效、产品展示、UI/UX动态演示、游戏视觉及风格化表达，帮助创作者和内容团队更快完成创意验证、视觉提案与内容制作。|

## 

## 商用级多场景内容生成

当视频模型具备更完整的能力，它也将覆盖更加丰富的创作场景，真正赋能真实的内容生产业务。

H3 兼顾文字、字幕、品牌信息、UI/UX、游戏及电商内容呈现，覆盖影视、广告、游戏、品牌、电商等高频内容场景。

它可以用来快速尝试短视频创意，帮助品牌探索不同视觉方案，让产品展示更具表现力，也让 IP 角色拥有更多动作和场景，还能支持视觉团队完成概念验证、分镜预览和内容提案。

### **品牌大片与影视内容**

> 电影预告片、TVC 广告片、品牌质感大片
> 
> 

|**提示词**|**输入文件**|**输出文件**|
|---|---|---|
|- （非完全Prompt，可自行补充）<br>- 图1至图4连续关键帧，模拟老式望远镜寻MINIMAX装置。开头虚焦手持晃动后快速拉近rack focus至图1，图间望远镜扫视转场（甩动、运动模糊、光学拖影、曝光闪烁）在最模糊处切换并迅速稳定重新对焦。全程固定双圆镜片遮罩（黑色羽化暗角、位置大小边缘虚化绝对一致无变形漂移）仅内部画面运动。图2布料随风克制飘动MINIMAX文字随布面起伏保持可读；图3人物如无意捕捉的时尚路人自然走动转身摆臂；图4人物调整眼镜或微抬下巴展现冷感松弛fashion campaign态度。红字随对焦轻微加载，初现略虚焦低透明度0\.3–0\.5秒内淡入变清晰（可微小纵向滑入或字距呼吸）切换前淡出或被运动模糊带走，禁旋转弹跳或大幅飞入飞出。Wes Anderson式窥视35mm胶片质感（轻微颗粒、柔和高光晕染、克制色彩、红字点缀），极简高级微带搞怪灵动，严禁新增人物车辆建筑logo，保持原图核心构图与MINIMAX装置不变。<br>|![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=MGEwZDY5NWFlMTg4OTRiNzRiYjA1Y2UwNmU5MDU2MjBfMDg3YjE0MWM5MzZhNzAyYmI0NjQ1MDZlMTAxM2RlNDdfSUQ6NzY2Nzg1MjQ5MDEyMTQxNTY0M18xNzg2MTczODM3OjE3ODYyNjAyMzdfVjM)<br>![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=ZGY0YzA2MmIzODM4MTg4MDBhOTcwODBlMzViODFlZmVfZGJjZWVmNzdlZjBhNmE0OTE2MTM3N2E1NzFjZmVkYTZfSUQ6NzY2Nzg1MjQ5MDU3ODY3NjcwMF8xNzg2MTczODM3OjE3ODYyNjAyMzdfVjM)<br>![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=Y2JjNDY0MjQ4OGRmNWI2YjYyZmU4NTlkYWFlNWFiNGRfMWQ1YTBjOWU3Yjc4NWFiNjhiYjAwMDIyNTAwYTY5ODlfSUQ6NzY2Nzg1MjQ5NTI1OTA2MTQ2Nl8xNzg2MTczODM3OjE3ODYyNjAyMzdfVjM)<br>![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=M2E4YzEwMGY4MjQ4MTNhYjQxNDRmMTliYmI5Mjk4NjFfZDVlYzY1YmMwMDM1YjFiNmU3N2I4M2FiYTkwYzQ0YTZfSUQ6NzY2Nzg1MjQ5NDIzMTg0OTkzMV8xNzg2MTczODM4OjE3ODYyNjAyMzhfVjM)<br>|\[多模态理解新1\.mp4\]<br>|
|- 史诗级太空歌剧院线短预告<br>- （非完全Prompt，可自行补充）<br>- 节奏更快，宏大但不拖。快速硬切、舰桥震动、强光爆闪、短黑场、跃迁冲击。文字是电影预告片式宽字距标题包装，字体不要纯白，要有克制发光和材质感、微弱边缘辉光。文字动效包含从深空暗部渐入、被星光扫亮、字距展开、残影、微弱发光、黑场闪现。 （非完整Prompt，可自行补充细节）|![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=NGZhM2FlYWE4ZmYxNzFjZGMyMGFjMWNjZjI2NzQ3NjVfNmMzNDg5MTJkMzJiNGYyZDI3M2U4ODU0OTM3Yzg4MGFfSUQ6NzY2Nzg1MjQ5Mjc2NDI1MzExM18xNzg2MTczODM4OjE3ODYyNjAyMzhfVjM)<br>|\[电影大片1\.mp4\]|
|- 科幻悬疑电影短预告<br>- （非完全Prompt，可自行补充）<br>- 写实电影感，高反差光影，节奏紧凑。图1作为整体氛围、风格参考。图2作为主角人物参考。 Shot 1 — 超广角建立镜头。巨大圆形宇宙门几乎占满画面，人物只是门前一个很小的背影，站在画面下方偏右。地面潮湿反光，门中心一片黑暗。镜头慢慢向前推进。大标题从黑暗边缘渐入，先模糊后清晰："THE STARS WERE LISTENING" 字体极窄、厚重、全大写，暗红混合铁锈红，带轻微颗粒和雾化边缘。 Audio: 深低频脉冲，远处金属轻震，文字清晰时一记轻 hit。 → Hard cut\. （非完整Prompt，可自行补充细节）|![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=ZGFiMjhiZjM0MDE2YWVhZWRkYzJlYmEyYmJmNGE3NWJfZjE0OGZmN2YzZjRiMmRjNGMzYzVkYTUwMWM5NzA2MjNfSUQ6NzY2Nzg1MjQ5NzQ5OTMxMTA2Ml8xNzg2MTczODM4OjE3ODYyNjAyMzhfVjM)<br>![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=NDVhYzkwN2ZlNWY0NTFkZjc4MDA3NWQ5MjgzMDVkNjhfMWMxYjgxNjU1MDRiMjQxMDQ2YWY4ZTIwZDhhYzQwM2FfSUQ6NzY2Nzg1MjQ5NzI4NTMwMzI2NV8xNzg2MTczODM4OjE3ODYyNjAyMzhfVjM)<br>|\[电影大片2\.mp4\]<br>|
|- （非完全Prompt，可自行补充）<br>- 制作一支 16:9 横版高级时尚品牌视频。整体氛围、场景和胶片质感参考图1；包袋资产参考图3；人物资产参考图2；品牌 ending logo 参考图4。这是一支卖衣服和包的时尚 campaign，整体气质要高级、冷感、克制，但剪辑不能无聊，要更灵动、更有时尚节奏。不要像普通剧情片，也不要像电商广告。核心故事依然很简单：荒漠公路和复古车旁，女人回到车尾，打开后备箱，取出黑色包袋，和站在车边的男人有一瞬间的安静关系，然后她拿着包离开。包和服装要自然融入人物行动里，成为角色气质的一部分。<br>|![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=MDM1MGJlOTAyN2M4NGYxZDkzZGE0ODRiZDJlOWMwZTRfOTNmYjYwYjQ4ZDg2YjQzYTgxZDI1ZGMzY2NkYjlmM2FfSUQ6NzY2Nzg1MjQ5ODY2NDczODA0M18xNzg2MTczODM3OjE3ODYyNjAyMzdfVjM)<br><br>![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=ZWNiZTk1ZmJjNGNlZGE4MjBmODgzNzI2MmNmYjRkMTRfZDQ1OTNmNzVjZWIwMDZkZDhkYjdlZjRkZDE2YTYxNWRfSUQ6NzY2Nzg1MjQ5ODcxMTAzODk1Ml8xNzg2MTczODM3OjE3ODYyNjAyMzdfVjM)<br>![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=NTFjMDU0YmU3ZWMwYjVhMGQ2OGVkYzAxODM0MTU2ODJfODRiMThmOGE0NTNjMWEwMDI0YTUwNGE2M2Q0NTcxMDlfSUQ6NzY2Nzg1MjQ5Nzk2NDY0OTY5N18xNzg2MTczODM3OjE3ODYyNjAyMzdfVjM)<br>![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=ZTljNTE1ODViODJlMzIwZjU4ZDUwZGQ4NDcxMjlmZGNfYmMyNjFkYzAxMGI5Y2IxMTgyNDI3MWM5YmNhYmMwY2NfSUQ6NzY2Nzg1MjQ5ODY0ODA1ODg1MF8xNzg2MTczODM4OjE3ODYyNjAyMzhfVjM)<br>|<br>\[海螺\_视频\_制作一支 16\_9 \_538443937841811462\.mp4\]<br>|
|- （非完全Prompt，可自行补充）<br>- 图1是整体质感、氛围参考，图2是人物外表特征参考。生成一支 15 秒 16:9 横版潮流时装短片。保持人物一致：白金色长发、窄黑色复古墨镜、黑色高光漆皮风衣、冷酷自信的时尚表情、火光映在皮衣表面的橙色反射。整体风格是胶片快切时尚广告，融合夜晚火场、黑烟、橙红火焰、VHS 故障、CCTV 广播中断、90 年代模拟胶片颗粒、扫描线、色差、漏光、闪白转场、画面轻微抖动。|![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=MWFjYWI4MGU3YjVlMzhlZTIwYzlkOWNlZDQ4MzQzOGFfOGJiMGIwZjBjNmVhOGM1Y2RjN2RkZDMwOTcxNmJiOTlfSUQ6NzY2Nzg1MjQ5NjIyODY4MjcwNl8xNzg2MTczODM3OjE3ODYyNjAyMzdfVjM)<br>![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=MjM5NmM2OTBjNjYwZWI5ZmY2MjZiMjY1MzNiZTNjOWRfY2MxNTViNzA5NWFjY2MyYTRhNmQ1NGZiN2Q4YjY4OTlfSUQ6NzY2Nzg1MjQ5NjIxNzg1MzE5NF8xNzg2MTczODM4OjE3ODYyNjAyMzhfVjM)|\[海螺\_视频\_图1是整体质感、氛围\_538385353669980169\.mp4\]<br>|

### 视觉创意与内容包装

> 创意短片、特效包装、审美 MV、视觉实验、热点内容及社媒素材
> 
> 

|**提示词**|**输入文件**|**输出文件**|
|---|---|---|
|- （非完全Prompt，可自行补充）<br>- 生成一支15秒16:9横版轻悬疑犯罪电影片头。整体风格参考这些图的视觉语言：复古日系动画片头、硬边剪影、漫画拼贴、非对称分屏、强烈几何色块、英文片头署名、少量日文片假名装饰、爵士犯罪气质。氛围是60%悬疑、40%爵士：神秘、酷、灵动、有都市犯罪感，不恐怖、不沉重，也不要变成欢乐爵士MV。片头动效要像动态图形拼贴：黑底线框先出现，分屏边界快速划出，色块和画格逐块贴入；人物剪影、道具特写、英文署名跟随鼓点依次滑入、弹出、遮罩揭示。不要普通写实剧情动画，要片头包装感。英文署名要清晰可读，允许有动效：细线框先画出，名字从框内滑入，字母逐个出现，被色块遮罩揭示，最后短暂停住。不要新增中文，不要乱码，不要让英文错拼。全片规则：所有英文署名和职位只出现一次。不要重复同一个职位，不要重复同一个人名，不要让同一个人担任多个职位。转场形式要丰富：圆形黑胶遮罩、车门竖切、人物长影擦屏、红线切割、巨大英文字母遮罩、分屏边框重组、色块硬切、画格逐块贴入。所有转场跟随鼓点，干脆、悬疑、灵动、有漫画拼贴感。不要柔和溶解，不要流体转场。BGM：原创15秒片头音乐，60%悬疑、40%爵士。以低音持续音、紧张弦乐拨奏、冷感合成器脉冲、低音鼓、稀疏爵士鼓刷、walking bass片段、低音萨克斯短句和短促铜管点缀组成。前2秒神秘低频和踩镲建立悬疑，第3秒进入低沉鼓点，第6秒加入爵士贝斯律动，第10秒出现短促萨克斯/铜管riff，最后2秒用紧张和弦加鼓点定格。整体神秘、酷、带犯罪感，爵士只占40%，不要太欢快，不模仿任何现有旋律。|![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=MzVhZGY5NzFjOWNhMzI5ZmEzOTNmYjM3NmEzMjhmMGZfNmRiMDZhYzU5YTAxMjljOTE0NzI3ZmRkOTg2ODg3NWJfSUQ6NzY2ODU3Mzk2NTk0MTcwNTY5Ml8xNzg2MTczODM3OjE3ODYyNjAyMzdfVjM)<br>![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=MmIzODQ0MGU0ZTA3ZDk0YWE3YzU2ZjNiMDIyYmYzNWRfMDA0NWJkNmRhZjgyMzM3MDY1MGIwYmVlNjRiODdkNTNfSUQ6NzY2Nzg4MDE3ODczMDg2Mzg1Ml8xNzg2MTczODM4OjE3ODYyNjAyMzhfVjM)<br>![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=NDY0NjcyN2EyNGU2NDJmOWI0YWY0Y2M4MjczYTZjMTlfZTY3ZDljODlmYTA4MzlkMDM1MzkyNTQwMTI5ZTJiZDNfSUQ6NzY2Nzg4MDE3NzUyMzQ5NDExOF8xNzg2MTczODM4OjE3ODYyNjAyMzhfVjM)<br>![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=NzczZmQ1ZTg1ZmZkMjMyN2FlNTZmYjM1MDk5MWM3YzVfYmNhMjFiZjA1Y2EzNDVmZjRiNTNlNzllNTg5MjUxZGVfSUQ6NzY2Nzg4MDE3ODU1NDg4MzA0MV8xNzg2MTczODM3OjE3ODYyNjAyMzdfVjM)<br>![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=YWU2ZGU2MDA4NmE0YTdjNTQxZTliMzBhZGYyOTE3OTdfOTZhYWVhM2NjNjkwYzEzZjdmMzJkZDEzZGIyOWRmYWZfSUQ6NzY2Nzg4MDE3NjgwNzIxODQxOF8xNzg2MTczODM4OjE3ODYyNjAyMzhfVjM)<br>![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=YjMxMWRiNmQyMThlOTNkYjAwMTZhOGRlMTJmYTMyOWVfMWNjNjA5ZmU5OTA0ZjJhZDg1ODE2NTZhZTM1MjcxM2ZfSUQ6NzY2Nzg4MDE3NzUyNzYwNjQ5N18xNzg2MTczODM3OjE3ODYyNjAyMzdfVjM)|\[final\-悬疑电影片头 \(1\)\.mp4\]<br>|
|- （非完全Prompt，可自行补充）<br>- 15秒、16:9横向视频。将傍晚小厨房的真人实拍与手绘发光动画融合在一起的影像。夕阳余晖还残留在窗边，生活感十足的小厨房里有一张旧木桌、洗到一半的马克杯、略微起雾的玻璃瓶，以及悬挂着的抹布。画面带有像用智能手机单手拍摄一样的细微手抖、近距离对焦时的犹豫、逆光造成的曝光波动，以及暗部略显粗糙的噪点。不要像广告影像那样精心整理，而是要呈现出像是在家中慌忙拍下某个不可思议事件的自然质感。禁止出现巨大的眼睛、裂开的嘴、獠牙、威吓、扑袭动作、突然黑屏和跳吓。声音只使用厨房室内环境声、抹布摩擦声、马克杯轻微碰撞声、水龙头水滴声、拍摄者的脚步声与轻微呼吸声，以及手绘生物柔和的电子音和小小的叫声。|纯文生<br>|<br>\[海螺\_视频\_15秒、16\_9の横\_538390013432676361\.mp4\]|
|- （非完全Prompt，可自行补充）<br>- 15 秒、16:9 横版短视频。实拍深夜自助洗衣店场景，融合手绘发光动画的混合影像。一间小型自助洗衣店，荧光灯微微频闪，店内摆放着运转中的洗衣机、塑料洗衣篮、老旧长椅，地面散落一只袜子，整体空间安静，带着淡淡的怀旧氛围感。手持手机单手拍摄质感，画面抖动明显；白色荧光灯造成曝光忽明忽暗；玻璃表面带有环境反光；镜头靠近物体时对焦存在延迟。画面不要像商业广告一样精致规整，整体质感如同深夜偶然闯入、追着奇异幻象随手拍下的真实纪实感。<br>|纯文生<br>|\[飞书20260728\-175157\.mp4\]<br>|
|- （非完全Prompt，可自行补充）<br>- 风格：dark\-pop / cyber\-grunge / rap 音乐视频，写实高时装质感，胶片杂志质感，高反差但不廉价。整体参考 90 年代末到 00 年代初独立杂志、复印纸、胶片扫描、地下音乐海报和 zine 拼贴美学。画面有粗颗粒、轻微胶片抖动、半色调网点、印刷毛边和扫描错位。剪辑节奏快，只使用硬切，不使用淡入淡出或柔和转场。 文字包装样式和质感参考图片。<br>|![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=YzU1NDZjOTZlMDRmNmI2OTEyNjhiOGQ3NTA5MjRjYmVfNjQzNjc5MzVlYjgzYzM5ZmZkYTRmNDZjOGU0NzljOWVfSUQ6NzY2Nzg1MjQ5MDU3ODU2MjMyMl8xNzg2MTczODM3OjE3ODYyNjAyMzdfVjM)<br>![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=YWQ4YWQ2YjAwNjJhZDg0NDQxYmI3Zjg4MTY3ZWZhMjRfMDk0NDU2YmFlOGYzMjY1NDYyYjI5MDdhZDg2ZGJkYzdfSUQ6NzY2Nzg1MjQ4ODA5MjM4ODMyNV8xNzg2MTczODM4OjE3ODYyNjAyMzhfVjM)<br>|\[d6deeef8d6e3\_denoise\_ids\_0\_final\.mp4\]|
|- 将视频1绿幕背景去除，变成类似视频2的童话感背景，背景元素需要完全匹配视频1的人物动作。修改视频1的人物光线，使之完全匹配背景。<br>|\[34fc0be96d70\_00\_视频1\_Mp8ybNSuBo\_greenscreen\_original\_alice\_girl\_wave\_10s\.mp4\]<br>\[Ref\.mov\]|\[4fde54fdffa6\_denoise\_ids\_0\_final\.mp4\]<br>|
|- （非完全Prompt，可自行补充）<br>- 制作一段 动态海报视频，整体保持原图的画廊白框、内框、红白黑配色、3D 手办感和排版结构不变，文字出来时配上灵动文字出场的音效。<br>|![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=MDBiOWQ5MzI2NjA2NTE2YTE5YzU2ZDAyNmRiZDQ5ZTZfOWY3OTU3MDU2M2MzYjU0MzkwM2VlZDE4MTZmY2IwMzJfSUQ6NzY2Nzg1MjQ5MTU2NDA1OTg1MF8xNzg2MTczODM3OjE3ODYyNjAyMzdfVjM)<br>|\[海螺\_视频\_制作一段 动态海报视\_538419531719503876\.mp4\]|
|- **手绘2\.0**<br>- （非完全Prompt，细节可自行补充）<br>- 视频整体<br>16:9 横向视频，总时长约 10～15 秒，全 4 个镜头，每个镜头约 3 秒，用节奏明快的硬切连接。画面是“海边小集市”的实拍智能手机影像，背景包含浅色摊位、遮阳棚、贝壳饰品、冰饮摊、海风吹动的布帘、远处沙滩和淡蓝色海面，整体氛围明亮、轻快、夏日感强。拍摄者右手以正常、自然、正确的写字握笔姿势拿一支细的青蓝色笔，从画面下部进入，每个镜头只指向一个现实对象，被指到的对象整体变成粗糙手绘 2D 动画，其他背景和未指向元素全部保持实拍。<br>|纯文生<br>|手绘<br>\[手绘2\.0\.mp4\]<br>\[手绘2\.0\-2\.mp4\]|

### 1\.3 动态图形、MG动画、AE特效

> \*官方小Tips：如果你在处理文字时遇到乱码问题，可尝试将文字以图片形式提供给 H3 作为参考图，并在提示词中明确告诉 H3——“这张内容必须按“图片”来理解，不能按“文字”来处理。” 通常能有效降低乱码情况。
> 
> 

|**提示词**|**输入文件**|**输出文件**|**后台链接**|
|---|---|---|---|
|- （非完全Prompt，细节可自行补充）<br>- 短片的准确开场画面。完整保留电光蓝背景、左侧白色“MiniMax”、中央浅蓝章鱼Logo和右侧白色“H3”。 图片2:章鱼Logo完成线性形变后的目标波形Logo参考，也是后半段贯穿画面的核心图形。严格保持波形Logo的路径结构、弯曲数量、圆角端点和整体比例。生成一支严格15秒、16:9、4K、60fps的MiniMax H3抽象科技MG品牌短片。短片表达H3从专用任务走向通用多模态模型的设计理念：语言、图片、视频和音频不再彼此隔离，而是被同一个上下文、同一套架构和同一根连续线连接起来。整体风格高级、简洁、灵动、有艺术感。采用大面积电光蓝、深黑蓝、浅青色和少量紫色色块，搭配干净的白色粗体文字。画面具有大量负空间，避免复杂图标和信息堆叠。全片的核心运动元素是一根浅蓝色连续线，以及位于线条前端的白色发光节点。|![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=ZmRiYjViNWRiZWM1NWVhOGNmYTFiNWNkMjIyZmE4YTBfYzNhZjhiM2NkMzBlODVlMTI5MmFmZTcxMjU0YmE4MTBfSUQ6NzY3MDEzNjI0MzU2NDc3NjM3N18xNzg2MTczODM3OjE3ODYyNjAyMzdfVjM)<br>![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=YTQyMTc2ZDk1ZTFjOTFlMWRmZTFlMzU5ZDM2YjEyZGRfNTlhYzUwMWI3NjQ5ZDY2ZjQ3Mjc0OGY4ZGFiZTkzZmNfSUQ6NzY3MDEzNjI0NDU3OTY1MDc0OF8xNzg2MTczODM4OjE3ODYyNjAyMzhfVjM)<br>|<br>\[MG动画1\.mp4\]||
|- （非完全Prompt，细节可自行补充）<br>- 为 AI 品牌“MiniMax H3”创作一支15秒高端平面动态图形品牌影片。【必须准确显示的文字】品牌名称：MiniMax H3<br>品牌 Slogan：Intelligence With Everyone<br>除以上两组文字外，画面中不得出现任何其他可读文字。<br>【核心创意】“One becomes everyone\.”<br>智能从一个微小节点出发，通过连接、共享与共同生长，形成属于每个人的开放智能网络。<br>以三种基础元素建立一套原创品牌视觉系统：<br>    - 一个极小的二维实心圆点<br>    - 字母“H”所代表的连接桥梁<br>    - 数字“3”所代表的三层智能轨道<br>    所有圆点、线条、轨道、字形和转场必须由这套基础元素连续演化。每次变化都具有清晰的视觉因果关系，形成统一的品牌视觉 DNA。||<br>\[MG动画2\.mp4\]||
|- 全中文文字动效<br>- （非完全Prompt，细节可自行补充）<br>- 整体为完全黑色背景上的中文动态字体实验影像。画面中只允许出现白色中文文字，以及极少量深红色文字错位或强调。不得出现人物、风景、照片、插画、图标、商品、Logo、3D 物体、英文标题、固定 UI、编号、计时器、边框、网格或任何装饰性图形。这不是普通字幕视频，而是以“中文文字本身”为唯一主角的高密度动态排版短片。文字在漆黑平面上高速出现、放大、旋转、压缩、碰撞、分解、增殖、反转、重组。整体风格像平面设计师制作的中文动态字体实验影像、文字运动 showreel、音乐活动开场视觉。气质黑暗、冷静、锋利、理性、无机质，略带攻击性，但保持高级、克制、统一。||\[字体动效1\.mp4\]||
|- Touch Designer动效<br>- （非完全Prompt，细节可自行补充）<br>- @视频1为唯一基础素材。严格保持原视频的人物、五官、服装、动作、场景、综合色、镜头运动、时长与帧率完全不变。只在原画面上增加TouchDesigner式动态追踪图形。<br>1. 所有矩形框的彩色填充透明度必须为0%。<br>2. 框内不得出现红色、青色或任何彩色蒙版。<br>3. 框内只能处理原视频相同位置的亮度、灰度、曝光和明暗关系。<br>4. 所有框只能是红色或者青色的完整、简单、连续的闭合矩形，四个顶点没有任何装饰或节点。                                               5\. 不允许一个框完整包含另一个框。||\[touch design\.mp4\]||

### AR现实增强创意视频

> 通过自然融合现实场景与虚拟内容，快速生成 AR 式品牌创意、巨物营销、户外视觉和社媒传播素材，让高成本的现实增强创意更高效地实现。
> 
> 

|提示词|参考图/视频/音频|输出文件|
|---|---|---|
|- 非完全提示词，可自行补充<br>- 使用上传的原视频作为唯一视频基础，严格按照原视频的真实镜头、真实手部动作、真实鼠标位置、真实城市十字路口、道路透视、斑马线、建筑、车辆、树木、红绿灯和自然日光来制作。不要重新生成一个新场景，而是在原视频上做 AR 实景合成与世界编辑效果。|\[IMG\_9503 \(1\)\.MOV\]<br>![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=Nzk3ZGI4NTYzNmE3ZjNiZDdkNzU1YzYxMmQ5NWEyYTNfNTYzMTY2ODhlOGQ3YmQwODAzYzc3ZjBkZDNjMjdjNTdfSUQ6NzY3MTI4NDQ2Njk1MDA2NTQ1MV8xNzg2MTczODM4OjE3ODYyNjAyMzhfVjM)<br>![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=NDMwM2UwMDJhZTBjYTQxNjJiM2M1NjI3YmM1MDgyNzRfZWI4M2RjNTNjYzQxZTZjNjlhMjFkNzI4MjU2NmEwNzdfSUQ6NzY3MTI4NDUwMTE2Mjc3Mzc0M18xNzg2MTczODM3OjE3ODYyNjAyMzdfVjM)<br>|\[1 \(3\)\.mp4\]<br>|
|- 非完全提示词，可自行补充<br>- 基于原视频1进行视频增强与特效编辑，保留原始构图、镜头角度、小猫的位置、动作节奏、电钻和电脑的位置关系。整体风格是搞笑短视频、夸张但真实感的生活场景，不要改变小猫的外形，不要替换主体，不要让小猫受伤。|\[原视频 \(1\)\.mp4\]|\[1 \(1\)\.mp4\]|
|- AR增强现实创意<br>- 主角出现在画面里的白色矩形框中，双手扶住框边，先探出头和上半身，然后一只脚踩住下方的白色线条，身体下压蓄力。镜头轻微推近，随后主角借力向上弹出画面。<br>切到 IMG1的空间。主角落在画面中的白色立体字体上方，坐在字体顶部边缘，双腿自然垂下。短暂停顿后，主角转头看向画面右侧的背景人物，形成一次清晰的视线互动。<br>随后主角朝画面右上角抛出一条细白色弹力绳，借力做一次弧线摆荡动作。镜头跟随主角做快速横向移动，保持平面海报空间穿梭感。<br>切到 IMG2 的空间。主角顺着弧线下落，踩到画面中的播放键上方。他用脚或手轻敲播放键，触发一次简洁的按压反馈。<br>最后切到 IMG3\.png。主角从播放键位置向画面右侧跑动，回到背景卡片中的原本位置并站定归位。全片使用快速横向跟拍、卡点闪切、轻微推拉和干净的平面空间转场。保持白色、灰色和原图设计元素，不添加血腥、打斗、武器、超级英雄标志或版权角色元素。<br><br>|<br>- 本案例是在MiniMax Hub上，使用H3模型\+Agent辅助完成（点击进入[MiniMax Hub体验入口](https://hub.minimaxi.com/)）<br>![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=YThlNTc2YTcxYzg0YzU5YzYwYzhmMTk1MWNiMjIwZThfNTczMjI1ZTI0YTlhOTQ1YTY2ZTMzOTBiMWYwZTExMDlfSUQ6NzY3MTQ4OTAyMDAwNTgyOTU2M18xNzg2MTczODM3OjE3ODYyNjAyMzdfVjM)<br>|\[AR动画\- Gino\.mp4\]<br>|

### AI 剧情内容创作

> 竖屏短剧、漫剧短片、角色演绎及AI 配音
> 
> 

|提示词|参考图/视频/音频|输出文件|
|---|---|---|
|- 非完全提示词，可自行补充<br>- 古装武侠悬疑短剧场景，16:9 横向电影画幅，夜晚竹林，冷蓝、墨绿、灰黑低饱和色调，薄雾弥漫，细雪在空气中飘落。整体氛围清冷、肃杀、克制，有江湖门派办案、秘密情报交接的紧张感。画面真实古装剧质感，浅景深，电影级光影，不要现代元素，不要字幕，不要文字，不要水印。场景：夜晚竹林深处，背景是密集竖向竹竿，远处有冷白雾光透出。前景有虚化竹叶遮挡，形成“林中窥视”的空间层次。冷白侧前方柔光照亮人物面部，背景逆光营造前暗后亮的电影感，浅景深，竹叶、雪花和背景竹林虚化成柔和散景。画面风格：古装武侠电影感，冷蓝墨绿雪夜竹林，浅景深，前景竹叶遮挡，人物面部特写为主，正反打剪辑，节奏克制但紧张。不要字幕、不要平台水印、不要现代服装、不要现代建筑、不要动画感、不要过度磨皮、不要明亮白天、不要喜剧表演。|![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=OWM4MjFjOWFiNjY5ZmEyZjM2ZDY1ZDFkMzc5YzMxMzVfYjFkYjNlYTYxNmY1ODkyNDdmNzRlZjA3Yjg4YjRhZmFfSUQ6NzY2Nzg3MDYyMDY2NzgwODczNl8xNzg2MTczODM4OjE3ODYyNjAyMzhfVjM)<br>![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=M2EzMWY2NjM4ODJlYmZhOTU5YjY0ZGFlOTc1ODI0YWJfYTAyZGRmOGY0ZTE2M2EzNDgyYTYyODQ3YzViZWEyZDJfSUQ6NzY2Nzg3MDYyMjg4NTc3NjYwMl8xNzg2MTczODM3OjE3ODYyNjAyMzdfVjM)<br>|\[海螺\_视频\_古装武侠悬疑短剧场景\_538750239088586759\.mp4\]|
|- 非完全提示词，可自行补充<br>- 室内家庭争吵短剧场景，竖屏短剧质感，真实真人表演，中式家庭/小饭馆室内环境，暖色灯光，背景有红色装饰和书法字幅，浅景深，情绪强烈，剪辑节奏紧凑。表演要求：真实短剧表演风格，不要夸张舞台腔。秦皓瑄的语气是愤怒、委屈、急切的反驳；中老年女性的语气是尖锐、强势、咄咄逼人的质问。两人之间有强烈对峙感，节奏逐步升级。画面风格：竖屏9:16，手机短剧质感，真人实拍感，浅景深，室内暖光，中近景为主，频繁正反打剪辑，背景保持生活化，不要科幻、不要古装、不要动画感。画面中不要出现任何字幕、文字、平台水印或贴片。|![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=ZDVmMmI2NDU4YmI1MzExYTM5MzU5YmRkYWQwMTk3MzRfYjNhOGViYjU5ODE1NjQ2N2FkZDRjMjE2ODg4ZDMzN2NfSUQ6NzY2Nzg4MjI0OTg0NDgzNzY2Nl8xNzg2MTczODM4OjE3ODYyNjAyMzhfVjM)<br>![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=MmNjNGNiYzFlMDFlOTM5ZGVmY2QyMDI1OWUwMzczYzNfNzgxNzlhOTAyYWI2MjRmNDE3ODY2YjU5YTEyZTU3YjJfSUQ6NzY2Nzg4MjI5NjUxOTc0MDM3OV8xNzg2MTczODM3OjE3ODYyNjAyMzdfVjM)|\[飞书20260729\-135143\.mp4\]<br>|
|- 非完全提示词，可自行补充<br>- 生成一支 15 秒、9:16 竖屏海外真人吸血鬼爱情短剧预告片段。男女主外形参考图1，场景参考图2。保持男女主身份一致，真人质感，高级短剧质感。整体故事：小白花人类女主误入古堡禁区，意外唤醒沉睡的吸血鬼贵族男主。男主发现她身上带着某种与古老战争有关的气息，因此对她产生强烈的控制欲和危险兴趣。女主害怕他，却没有彻底屈服，反抗他的压迫。整体风格：海外 ReelShort / DramaBox 吸血鬼爱情短剧预告感。暗黑浪漫、危险吸引力、宿命感、强控制感、阴郁压迫、高光反转。画面高级、克制、紧凑，像爆款短剧的前 15 秒钩子。不要血腥，不要廉价恐怖，不要万圣节感，不要现代街头感。画幅：9:16 竖屏构图，适合 TikTok / ReelShort / DramaBox。人物以中近景、近景、特写为主，竖屏里要突出脸、眼神、压迫感和关系张力。|![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=ZDQwNmM0NDlhOTY5MzFhMzVkMmNhN2U0OTlkMWU3NjlfYmE2MDFiY2YzYjA1Yzk5Y2YxNjg3NjNlNmRlNDNlOGNfSUQ6NzY2Nzg4MjY3MDc0MzA4MDE3Nl8xNzg2MTczODM3OjE3ODYyNjAyMzdfVjM)<br>![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=MjQyOTNiODI1ZTI3ZjA0MmMwOWEzOTA2ODc2N2U4MjRfZDhmMzFjODMwZDZiNTVmN2ZjNDdhOGVhMzBkYmI1MDVfSUQ6NzY2Nzg4MjcxNjEwNTA1MTExMl8xNzg2MTczODM4OjE3ODYyNjAyMzhfVjM)|\[海螺\_视频\_生成一支 15 秒、\_538749180689526786 \(1\)\.mp4\]<br>|

### **产品与电商营销**

> 产品展示、卖点视频、品牌及投流素材
> 
> 

|提示词|参考图/视频/音频|输出文件|
|---|---|---|
|- **（非完全Prompt，可自行补充）**<br>- 生成一支 竖屏 9:16 高级时尚眼镜广告片，整体参考所给视频的分镜节奏、剪辑速度、白棚质感和冷峻时尚氛围。画面是极简白棚，无缝白色背景，强烈的高定广告感，干净、简约、帅气、先锋、国际一线时装大片质感。主视觉人物参考 图片1，两位全身女模特，一个黑人女模特，一个欧美女模特，保持她们的服装高级感、身体姿态、白棚光影、时装秀场气质和整体冷峻态度。两人都佩戴未来感高级眼镜，眼镜设计参考图3，强调包覆式弧面、锐利几何猫眼/护目镜混合轮廓、镜面反射、流线型镜腿、高级时尚配饰质感。两个人物的外貌细节参考图2。<br>|![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=NjYyNDg4NmUxYjYwOWEyMzc1MTdkZDk1OGRkMWZjYjJfMTAzNmI4NjM5OTA0YTJkZDVmYzRmOGIwNzdhZDNjMjRfSUQ6NzY2Nzg4ODMyNjA3NDE0MTY0M18xNzg2MTczODM3OjE3ODYyNjAyMzdfVjM)<br>![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=MzMzZGIyYWFlMDVjNjU1NzFmOWZmMTcyMTQ3YTJhYjFfNWMzZGNjMDEyZmQxOTk0NDRhZDU5MDQzNjg4MWYyYWNfSUQ6NzY2Nzg4ODQwODU3NzcyMzMyNF8xNzg2MTczODM3OjE3ODYyNjAyMzdfVjM)<br>![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=ZGY1MTRiMjY2OGM3NTY5ZmYxMTY0N2Q4MDAwZjY0MTdfNGM5YmMzMjEyYTk2NWVlZWQ3YTdiOWVjODYxYjA4YTJfSUQ6NzY2Nzg4ODUwNTgzODA0NjQ1NV8xNzg2MTczODM3OjE3ODYyNjAyMzdfVjM)<br>|\[海螺\_视频\_生成一支 竖屏 9\_\_538380586306613254 \(1\)\.mp4\]|
|**产品功能理解及视觉展示**<br>- **（非完全Prompt，可自行补充）**<br>- 高级办公室Herman Miller黑色人体工学椅360度展示。透气网背特写空气流动可视化。腰部支撑\+人体工学曲线工程动画。多维度调节扶手/座椅高度演示。设计师/程序员/创意人员长时间办公场景,姿态舒展自如。久坐不累3D骨骼支撑示意图。空间美学室内陈列。结尾"灵感与舒适同时在线"字样浮现。高端简约、冷色调、专业未来感、慢节奏运镜。产品详情参考图1，产品图参考图2。<br>|![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=ZTE4NDhkN2Y0NzkwOWIzZTA5YzdkMGJlMDUyYWQyMDlfZjQ2NGE0YjNhN2JmZGIxNDFlNjFjZGM2YjQzZWZiMjNfSUQ6NzY2Nzg1MjQ5MjEzMDI0MTQ5MF8xNzg2MTczODM4OjE3ODYyNjAyMzhfVjM)<br>![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=NTI1ZGQ5NzU0ZWIyMDJiNjA1YmQwMzAxOTQ2OTM4M2RfZmQyMDJiNzFlNDNkMWNkOTQ1NzIyNWViMmI3NzE3NGFfSUQ6NzY2Nzg1MjQ4OTQ5MjYxNDA3NV8xNzg2MTczODM3OjE3ODYyNjAyMzdfVjM)<br>|<br>\[fd5118f8f1dd\_denoise\_ids\_0\_final\.mp4\]|
|**美食产品宣传**<br>- **（非完全Prompt，可自行补充）**<br>15 秒，16:9 横屏，完整模仿高级感品牌新品发布视频的视觉语言：纯黑背景、棚拍级灯光、超慢速旋转特写、极简巨型无衬线标题、空灵电子配乐。产品是——一只完美烤制的北京烤鸭。<br>字体必须极简、留白充足、统一使用纤细无衬线字体；中文不能有错别字。禁止：卡通风格、杂乱背景、水印。<br>||\[海螺\_视频\_15 秒，16\_9 \_541014619796496390\.mp4\]|

### **数字体验与游戏创意**

> 游戏 UI、网页 UI、产品界面、交互演示、功能展示及体验动效
> 
> 

|提示词|参考图/视频/音频|输出文件|
|---|---|---|
|- 角色参考图1，UI风格参考图2。 \[0 秒\-2 秒\] 高角度俯拍。角色坐在高饱和度的亮紫色地面上，参考为图1，抬头看向摄像机。右侧显示游戏菜单 UI：开始新游戏 \(START NEW GAME\)、继续游戏 \(CONTINUE, 高亮显示\)、设置 \(SETTINGS\)、退出游戏 \(EXIT GAME\)。左上角显示玩家资料 MINIMAX。光标点击“继续游戏”。 \[2 秒\-4 秒\] 平滑变焦至她的右臂。UI 面板从右侧滑入，“右臂装备 \(RIGHT ARM EQUIPMENT\)” 面板出现。选中高亮显示 “幻影之握 \(PHANTOM GRIP\)”，随后滑动至 “时空之爪 \(CHRONOS CLAW\)”。她的右手机械地重新配置，手指分开，新的爪状指节锁定到位，青色 LED 灯闪烁得更亮。 \[4 秒\-7 秒\] 摄像机平滑地绕到她的左侧。新的 UI 滑入 “武器定制 \(ARMAMENT CUSTOMIZATION\)” 网格，显示手部、前臂、肘部、上臂组件。选区快速循环切换部件。她的左臂逐段拆解：前臂板脱落，新装甲滑入，肘关节更换，手部重新配置，更换过程中可见暴露的线路和活塞。 \[7 秒\-8\.5 秒\] 摄像机拉回至中景。确认配置 \(CONFIRM CONFIG\) 按钮闪烁。点击。所有 UI 面板向内收缩消失。角色双腿解开，调整姿势，现在放松地坐着，单膝立起，义肢手自然抬起并完成配置后的轻微动作展示。 \[8\.5 秒\-10 秒\] 底部出现加载 \(LOADING\) 条。从 0% 快速填充至 100%。高饱和度的亮紫色环境开始变暗，阴影从边缘蔓延，温暖的金色光芒渗入。 \[10 秒\-15 秒\] 当她起身时，完整的环境在她周围加载。密集的赛博朋克贫民窟显现，霓虹灯闪烁，潮湿的街道反射着光芒，人群涌动，摩托车穿梭，错综复杂的电线，堆叠的建筑向远处的未来派摩天大楼延伸。摄像机稳定在第三人称视角，位于她身后，展示她的背部。HUD 元素淡入，右上角显示小地图，左下角显示生命值和弹药计数器。任务标记出现。她迈步走进街道。|![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=NzE3ZGMzNDliMGY2YTYzYTI3NDkxZjJiODNjMjlkZjFfZGI2NDBjYTI5Mjg1NzYwMzcxOTdiNzU4NmY3YWQ4YmRfSUQ6NzY2Nzg1MjQ5MzcwMzM1MTU5OF8xNzg2MTczODM4OjE3ODYyNjAyMzhfVjM)<br>![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=Y2Q0OGE1NmMwNTdlOTBhNzNlMzBlNzRhZjQzMDY1YjdfMzE5OGViOWM4OTUzMThmZWQxODZhMWMxYjdmNTY5NjdfSUQ6NzY2Nzg1MjQ5Mzc3ODk4MDAyMF8xNzg2MTczODM3OjE3ODYyNjAyMzdfVjM)<br>|<br>\[bfb4ac033274\_denoise\_ids\_0\_final\.mp4\]<br>|
|- **（非完全Prompt，可自行补充）**<br>- 一个网站页面，网站页面UI设计，网站动效，视频展示了流畅的网页向下滚动效果。一个极具爆发力与动感的产品官网风格产品落地页 UI/UX 演示视频，核心展示主体是该产品图片1。页面采用粗犷有力、倾斜的超大号无衬线字体进行张扬的排版。背景有极具速度感的动态光影、暗色碳纤维或运动透气网眼纹理在交织变换。视频展示了节奏紧凑、充满力量感的网页向下滚动效果，以及鼠标悬停时强烈的视觉放大与颜色反转等 UI 交互动作。<br>|![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=Y2I0YWEzZTU3OGY3NzJkOTc1MjU2MjJmMGJiMDE3ZDlfYzkxZTY5YWIyOWQxNmEwNjA3NmEzMDUyMDQ3YzNlYTNfSUQ6NzY2Nzg1MjQ5NTI5MjU4Mjg2MF8xNzg2MTczODM4OjE3ODYyNjAyMzhfVjM)<br>|\[ceb748012c82\_denoise\_ids\_0\_final \(1\)\.mp4\]<br>|
|- **（非完全Prompt，可自行补充）**<br>- 模拟网站UI设计，先是上面的标题向下滑动出现，然后是下面的文字栏向上划出，汽车灯由暗变红<br>|![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=MzRhM2ZmNmY2MTEzMzkzOTJiZWRiZDZkZGMxMWRmZWNfYmZkZTI0NzczM2ZkZmY4NmQ4Zjk1OGJiMWJmMzk1NDFfSUQ6NzY2Nzg4NjY0MDY4OTQzMzc4MF8xNzg2MTczODM4OjE3ODYyNjAyMzhfVjM)|\[1909c51fafc8\_denoise\_ids\_0\_final\.mp4\]|
|- （非完全Prompt，细节可自行补充）<br>```XML<br>生成一段10秒、4:3 横向构图的游戏视频，整体像一个极简可爱的 2D 手绘反应游戏界面。画面保持固定镜头，不要运镜，不要缩放，背景干净，保留温暖纸张质感和蜡笔 / 彩铅手绘线条。主角始终是同一只皮皮的小比格犬：圆润 Q 版身体、短腿、大耷拉耳、圆润长吻部、短翘尾巴、半眯慵懒又欠揍的表情。小比格身体可以像橡皮筋一样被夸张拉伸、压扁、拱起和侧闪，但身份和画风始终一致。<br>视频是一个“按方向键躲手掌”的快节奏小游戏操作流程。画面底部始终有一排手绘方向箭头 UI，箭头包含上、下、左、右四种方向。每个操作节拍开始时，对应方向箭头迅速变成实心高亮，并出现手绘圆圈涟漪、短促放射线、小星星或爪印反馈。顶部保留轻量手绘 HUD：左上角三个小爱心，顶部中间一条细细的手绘进度条，右上角一个小骨头图标和少量涂鸦装饰。装饰要稀疏可爱，不要遮挡主角、手掌或方向箭头。不要出现任何可读文字，不要现代电子 UI，不要真实摄影效果。<br>核心玩法规则：<br>图1，当底部“上”箭头高亮时，手掌从画面下方向上伸出，小比格必须向上拱起身体躲开，身体形成夸张半圆桥。<br>图2，当底部“下”箭头高亮时，手掌从画面上方向下压来，小比格必须压低身体贴地躲开，前半身扁平，后半身翘起。<br>图3，当底部“右”箭头高亮时，手掌从画面右侧水平伸入，小比格必须向左拉长身体躲开，耳朵甩飞，前爪抓地。<br>图4，当底部“左”箭头高亮时，手掌从画面左侧水平伸入，小比格必须向右滑行躲开，身体像弹簧一样压缩侧闪。<br>所有手掌方向、箭头高亮方向、小比格躲闪动作必须一一对应，不能错位。<br>```|![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=NDczZDE2ZmY2OTM1Njg2Yjk1MjkwMjcyMjEwNzJlYTdfMDZjYTk2MDE3ZmE0ZDBlNTdjODc4YTY2YTRkZWRhOGVfSUQ6NzY3MDEzNjY2MzI5ODk2ODUyNl8xNzg2MTczODM3OjE3ODYyNjAyMzdfVjM)<br>![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=MjhiZjBlMTcxN2JhMGE4MzQ1ZWNhZTE4MGM3Y2NkYTFfNjUxNTdmZmRjNmViYzNhYTQxOGVmMjVkMjA4ZWM3MWJfSUQ6NzY3MDEzNjY2NDg2NTcwNTE0MF8xNzg2MTczODM3OjE3ODYyNjAyMzdfVjM)<br>![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=ODE1MTliZWQ3MGE5ZTA3ZjUzMzUyNDhlODU1MGE3ZTJfNjkwOTQ4M2NhM2UwODAyZjI4ODhhNjZmMWExYTgzMjVfSUQ6NzY3MDEzNjY2MjY5MzE4NjUyNF8xNzg2MTczODM3OjE3ODYyNjAyMzdfVjM)<br>![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=Y2ZlNWJhOGFjNjQ5NTkzYWMyYzBmMjc4YjdiODRiZWNfNGIzMDIxMWQ1YmI4NWY2MDBlMGE4NmQ3Mjg4YWNkOWFfSUQ6NzY3MDEzNjY2NTU4NzAxMDg1OF8xNzg2MTczODM3OjE3ODYyNjAyMzdfVjM)|\[3\.mp4\]|
|- （非完全Prompt，细节可自行补充）<br>```XML<br>使用 Image 1 作为精确的 UI / 布局 / 界面风格参考。<br>Image 1 中的鼠标光标也作为精确的鼠标样式参考：鼠标光标必须保持 Image 1 里的大小、形状、比例、半透明质感、柔和发光边缘和精致高级感。不要生成过大的系统默认鼠标，不要生成粗糙黑白箭头，不要生成多个鼠标。<br>使用 Images 2–5 作为精确的灵宠参考，并按以下方式映射：<br>Image 2 = card A = MIRRA POD<br>Image 3 = card E = LANTERN<br>Image 4 = card F = MOSS MITE<br>Image 5 = card C = VELI KIT<br>生成一个 15 秒、16:9 横版视频。<br>镜头完全固定，不要推拉、摇移或切镜头。<br>保持 Image 1 的界面结构、排版、面板、字体层级、图标、圆角、卡片网格和整体构图稳定、优雅、清晰可读。<br>界面气质是高级、极简、梦幻的数字灵宠图鉴。<br>不要新增无关文字，不要乱码，不要 UI 扭曲，不要界面漂移。<br>整体风格：<br>梦雾、柔焦、微绒、半透明、轻发光、高级极简。<br>四只灵宠都要非常可爱、灵动、软萌、有灵气。<br>动作要干净、精致、有互动感。<br>界面本身保持稳定，只动画化鼠标、选中态、主标题、当前主展示灵宠和少量技能特效。<br>```|![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=NzQ3OTMxN2ZjMTlkZTg5NmY5ODg5ODEwMmE4NGY2OGRfNDRkNmRmZjhiMmIzY2Q3ZWE5ODRjYTcxZTFmNzU0YjdfSUQ6NzY3MDEzNjY2NTUyNTc1MDk4M18xNzg2MTczODM4OjE3ODYyNjAyMzhfVjM)<br>![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=MTdjZmM2NmNlYWUxMzQxNzNhMWQxMzFiYTkyNTJlMGZfNGFhYWQxNzNiMThlMWIyYzM2ZmNlOGQxODkyNzM1N2ZfSUQ6NzY3MDEzNjY2NTI0NzIyMzA1OF8xNzg2MTczODM4OjE3ODYyNjAyMzhfVjM)<br>![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=ODA1OGE4MWZlNjIyNDcxMTBkOTQ5ODIyM2U1M2FlODFfODJmYjZjNTVmYmIyZDY3NjFjYzBjNjRhZjQ1OTc0MGJfSUQ6NzY3MDEzNjY2NTM3NDgyMTM1OV8xNzg2MTczODM3OjE3ODYyNjAyMzdfVjM)<br>![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=ODgzMTM0ZDNjMzA4MjBmMGU5NmUwYWRhZDExMGU5MDVfZDBlNmJlNDQ2NTg2MzA2ODkxYWYyZTMwMTZkZDUwYmVfSUQ6NzY3MDEzNjY2MzY1Nzc3ODQ1OV8xNzg2MTczODM4OjE3ODYyNjAyMzhfVjM)<br>![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=ZThiYzk2ZmNkNGVhYTMwZWFjMTMyNmEwYzI4ZWEzZjVfOThlNTlmNDRhOGEwMTE2M2U5ZjBjMWU1MjYzMjg0OWJfSUQ6NzY3MDEzNjY2MjkxOTcxMTkzMF8xNzg2MTczODM3OjE3ODYyNjAyMzdfVjM)<br>|\[1\.mp4\]|

### 硬件、实体工业、具身智能演示

|**提示词**|**输入文件**|**输出文件**|
|---|---|---|
|- 固定镜头，机器臂下降，抓起红色方块，向前移动一段距离后放下<br><br>|文生视频<br>|\[Hailuo\_Video\_机器臂下降，抓起红色方块，向前移动一段距离后放下\_539561186482315272 \(1\)\.mp4\]<br>|
|- 精准替换场景背景<br>- 改背景的提示词：将原视频中的桌面替换为标准办公室工位办公桌，背景整体替换为带有百叶窗与金属文件柜的办公环境。新办公桌的透视比例需与原镜头完全匹配，桌面材质需自然承接原视频的光影投射，边缘阴影与高光方向必须与原场景光源严格一致。背景百叶窗与文件柜的景深虚化程度需与原视频焦点对齐，保持原有空间纵深感。在此过程中，原视频的镜头运动轨迹、机械臂的完整运动时序与速度、画面中其他物品的相对位置与空间遮挡关系、以及整体光照氛围必须保持 100% 不变，确保替换元素与原画面无缝融合。|<br>\[Hailuo\_Video\_机器臂下降，抓起红色方块，向前移动一段距离后放下\_539561186482315272 \(1\)\.mp4\]|\[Hailuo\_Video\_将原视频中的桌面替换为标准办公室工位办公桌，背景整体替换为带\_539564842892009473\.mp4\]<br>|

### **动画与风格化影像**

> **游戏 CG、角色 PV、动漫 PV、风格化动画、二次元视觉及 IP 内容**
> 
> 

|提示词|参考图/视频/音频|输出文件|
|---|---|---|
|- **（非完全Prompt，可自行补充）**<br>- 黏土动画风格。 狂奔的狐狸冲到了悬崖边缘，毫不犹豫地腾空而起，在巨大的熔岩峡谷上方完成了一个极具张力的、慢动作的英雄式飞跃。镜头在半空中从狐狸的腹部下方极速掠过（大动态运镜），完美展现出深渊的恐怖深度，以及狐狸黏土身体在空中极致舒展的动态瞬间。<br>|![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=OWIzOGQ2ZjJjMzMwZTk4MmMzMzA5MWM1N2Q2OTYyZjRfYzZmZmFiZGMyOTFlNWMzNDhhYWU1N2VhYzFjYTUzYWZfSUQ6NzY2Nzg1MjQ5MzA3MDQwNDg5OV8xNzg2MTczODM3OjE3ODYyNjAyMzdfVjM)<br>|\[92058e16a68c\_denoise\_ids\_0\_final\.mp4\]|
|- **（非完全Prompt，可自行补充）**<br>- 使用 图2作为固定人物参考，保持黑色半扎长发、银色镂空发冠、黛蓝发带、浅色层叠汉服、半透明蓝色外袍、深蓝腰封、银色花形扣饰和长流苏一致。使用 图1作为镜头分镜、节奏参考。画面为高质量 4K 16:9 国风 3D，电影级仙侠质感，热血、庄严、宿命感强。镜头依次表现分镜中的内容，确保每个分镜之间运镜、切换自然，不能像ppt一样。人物露脸只能是近景或特写，远景只能是背影、侧背或环境空镜，不要正脸远景。<br>|![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=ZTU2ZTk5MGYxOTk5Y2U0NjE4Y2U5MzFkOWQ2NjBlMDlfM2ZjNjM4YTMwMjE4NDRjNDdiYTI2ZWRkNDkwYzE0MDJfSUQ6NzY2NzkwOTQ2NTcxMDEyMDIwMl8xNzg2MTczODM3OjE3ODYyNjAyMzdfVjM)<br>![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=Nzk0MDFiZGRjYWVhOTE0MGYzOTkwZTQ3Zjk3OGMyNzdfMzE0NmNkNTJjZmM5ODViZTQ2MWYwYmExMzgwNThiYTJfSUQ6NzY2NzkwOTQ2NDM1Mjk1MTI3Ml8xNzg2MTczODM3OjE3ODYyNjAyMzdfVjM)|\[fb80932981b4\_denoise\_ids\_0\_final\.mp4\]<br>|
|- **（非完全Prompt，可自行补充）**<br>- 生成一支 乙游男主角色 PV。 角色参考图： 使用图2作为严格的角色身份参考。请保持同一个角色脸、发型、体型比例、服装设计、材质细节和乙游 CG 质感一致。 <br>|![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=NzU3NDU0NWM4OTljYzQwOGY5ZTEzZDgxMmVmMDUwYjdfMmM3ZjE1NzZlYmQ2N2IzOWU4M2QyOGM5YzJiYjFlYWVfSUQ6NzY2Nzg1MjQ5MTY5MjM3OTExMl8xNzg2MTczODM4OjE3ODYyNjAyMzhfVjM)<br>![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=MDBmMTA5OWY0Mzg5ODRjY2FkMjNiNWEyYWVkYWIyNmVfNzQ4ZjE0YmYzNzZkOGE1YjkxMjcwY2E0NTdiNmFiODNfSUQ6NzY2Nzg1MjQ5NTYyODA2MTk5Ml8xNzg2MTczODM4OjE3ODYyNjAyMzhfVjM)|\[3da4601486ec\_denoise\_ids\_0\_final\.mp4\]|
|- **（非完全Prompt，可自行补充）**<br>- 镜头：第一人称视角 · 眼平高度 · 手持游戏镜头 画面： 画面模拟玩家正在操作一款现代战争 FPS 游戏，双手持突击步枪在军事基地外围缓慢推进。 玩家沿着掩体旁的道路向前移动，准星扫过前方通道，短暂停顿后向远处目标点开火几发，随后继续向前压进，像普通玩家实机操作画面。 光线： 现代军事基地的冷色自然光与烟雾火光交织，画面写实清晰，金属枪械和战场尘雾有 3A 游戏质感。 运镜： 镜头随玩家移动产生轻微手持晃动，先缓慢前进，再小幅左右观察，开火时有轻微后坐力抖动，最后继续稳定向前推进。|![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=Y2JiNGVmMmQzNDFlY2FjZWM0NmVhYzIzNjEwMTEwMTFfM2JiZWZhYjQwM2NkM2U0YmRjOWY3NDBmYWZkOTI3MzNfSUQ6NzY2Nzg1MjQ5NTI2NDg0NDc0Ml8xNzg2MTczODM3OjE3ODYyNjAyMzdfVjM)<br>|\[飞书20260729\-181004\.mp4\]|
|**人机互动游戏**<br>- **（非完全Prompt，可自行补充）**<br>- 使用第一张图作为首帧，第二张图作为严格尾帧，生成一段乙游视觉小说界面转场视频。  整体感觉：高端中文乙游恋爱互动界面，演出前后台的暧昧瞬间，从“选择来看他的演出”自然过渡到“韩序被女主的话吸引，露出饶有兴趣的反应”。UI 文字、选项、对话框都以乙游式精致方式出现，转场丝滑，情绪暧昧但克制。<br>|![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=YzY2NGRmZGI5NjU1MjYzMTMwMjUyMzEzNDM5OTliZGZfYzFhNjcxMGNiMTMxMzY2Yjg4ZTNmNjdkMDY5MDYzMTBfSUQ6NzY2Nzg1MjQ5NDkxNTE2MTA0OV8xNzg2MTczODM3OjE3ODYyNjAyMzdfVjM)<br>![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=NjI1YjU4ZjQwYmE2YWEzMzI5MGU1NTMzMjNmNTM1ZTFfM2QxZjY2MjgxY2U1YTYxNjlkYjVmOTJmMjRmNDgzM2JfSUQ6NzY2Nzg1MjQ5NDA2ODM1NDI2Nl8xNzg2MTczODM4OjE3ODYyNjAyMzhfVjM)|\[bfae4aab6e47\_denoise\_ids\_0\_final\.mp4\]<br>|
|**情景式演绎**<br>- **（非完全Prompt，可自行补充）**<br>- 主角是图1，电影级、写实画风，实拍现实画风。 正面近景拍摄视角，画面只聚焦于男主与女主的上半身。女主面部视频中基本不露出，她身穿露腰露背的红色连衣裙，只偶尔出现肩颈、手臂、腰线、裙摆和手部细节；男主身穿剪裁极佳的黑色高级定制衬衣。场景是在图2暧昧氛围的红黑色调室内，整体光线昏暗、低饱和、奢华、克制，后景微微虚化，红丝绒沙发、黑金大理石边几、暖色低光源共同营造成熟暧昧的约会氛围。 画面发生在图2的红丝绒沙发前。男主坐在红丝绒沙发上，姿态慵懒而从容，身体微微后靠，衣料质感高级、细腻。沙发旁是一张奢华的黑金大理石边几，上面放着一个精美的水晶玻璃杯，杯内盛着琥珀色威士忌和几块正在慢慢融化的冰块，杯身隐约可见细腻水珠。画面中能听到冰块轻轻碰撞玻璃杯的声音、雪茄燃烧的细微声、室内轻微空气流动声、衣料摩擦声与克制的呼吸声。 |![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=MDFlNTJmZDZhNTlmMWI3MDY1YzY2OTE4NjJhY2YzOGJfMDhiNjYxNTlkZGUzZjdmYjM1ZTE0NjNmYTAyYmI0MjdfSUQ6NzY2Nzg1MjQ5MTQ1NjEyMTgzNV8xNzg2MTczODM4OjE3ODYyNjAyMzhfVjM)<br>![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=MWUyMDE1ZDFiNDIyYjY4NjdlNDlkZjE1MWVmMTlmMTdfOTQ5YTViYWRkZjMwZjJkZjgxMmIzNTdhOTQ1NDFhMjZfSUQ6NzY2Nzg1MjQ5NDE4OTc0MzA3M18xNzg2MTczODM3OjE3ODYyNjAyMzdfVjM)<br>|\[3f09c05ee348\_denoise\_ids\_0\_final\.mp4\]<br>|
|**二次元风格**<br>- **（非完全Prompt，可自行补充）**<br>- 纯二维赛璐璐 × 抽象MG，动态平面海报感。整体为黄色高反差视觉系统，以金黄、琥珀黄、柠檬黄、黑白为主，少量金属灰辅助；红色仅限反派沙发、酒液、危险信号。城市完全平面化，使用线稿管道、网格、矩形块、切片、刻度、符号化建筑拼合，不出现立体3D、不做电影透视。允许倾斜、翻转、压缩、变形、反相、剪影、斜向遮罩、图形匹配转场，全程像一张持续运动的平面海报。||\[海螺\_视频\_风格设定： 纯二维赛\_540976941206548484\.mp4\]|



## **原生多模态理解与生成**

H3 支持文字、图片、音频、视频等多种输入，将所有素材视作统一上下文，理解信息、声音、情绪、画面与表达意图之间的关系，进而实现从内容理解到视听融合的一体化创作。

- **多素材联合参考：** 文字、图片、音频与视频自由组合，共同参与内容生成

- **角色、动作与镜头参考：** 参考主角形象、人物动作、镜头运动与画面构图

- **音色迁移与克隆：**参考音频音色，丝滑更新角色声音

- **氛围与剪辑理解：** 参考原视频的视觉风格、叙事节奏、声音氛围与整体剪辑感

**语言支持与本地化表达**

- 支持多语言提示词输入与输出

- TTS （文本转语音）精准覆盖 11 种语言，包括中文、英语、日语、韩语、法语、德语、西班牙语等

- 更多语言可衍生探索，如阿拉伯语、泰语、印尼语、印地语等40多种语言

- 适合海外品牌传播、多语种广告、跨语言短片和本地化产品介绍等场景

### **多素材联合参考**

文字、图片、音频与视频自由组合，共同参与内容生成

|**提示词**|**输入文件**|**输出文件**|
|---|---|---|
|- 参考剪辑<br>- 图1图2图3图4图5图6，严格参考示例视频视频1的镜头节奏、转场风格及音乐。<br>|图1\-6<br>![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=YWEzNjg1NjUzYTU3NjgxZGJjZTM4N2M0ZGFlNmU4YmNfMWQwMjc2YmNiNzYwNWFlOTE3ZjFiY2FlODlmNDYzOWRfSUQ6NzY2Nzg1MjQ5MzU2OTE5OTQwNF8xNzg2MTczODM3OjE3ODYyNjAyMzdfVjM)<br>![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=YWE4NjlhYmMyMGY5MjUyOTVmMjE2MTcxNmNiNjVkOTVfYmFmNDJiMDVlOWRkNzQ4MmMxMWRkZmRmNmFlMWU4YThfSUQ6NzY2Nzg1MjQ5NTExNjQzODc5OF8xNzg2MTczODM4OjE3ODYyNjAyMzhfVjM)<br><br>![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=N2Y2YTk2YjFlZWE1ZTg2MjM1N2QzYjJkYzg0YmQ3NWFfN2FmOGE4YjE3ZDA4YjE1MDU5NGQ5ZmQ3NDIyNDY0NjNfSUQ6NzY2Nzg1MjQ5MzUzNTY2MTI0NF8xNzg2MTczODM4OjE3ODYyNjAyMzhfVjM)<br>![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=NzY5NDVhNDA5YWEyMjYxOGFlNmY2N2JmNjQ3MmIyMmFfMjA4Zjk0YTNkNTNmNmFiMjAzMzY3MTk2MzQzYTkzZDRfSUQ6NzY2Nzg1MjQ5MTU2NDczMTU5NF8xNzg2MTczODM4OjE3ODYyNjAyMzhfVjM)<br><br>![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=ZWJiOWMzMTljOTNkNzY4NjQxNzFlZWUwNmRiY2JkZjhfMzYwNWE2YWZiMDlhNWZmNjUxNjNhZWFhMTRjY2JlOTlfSUQ6NzY2Nzg1MjQ5MTcyODUzODgwM18xNzg2MTczODM3OjE3ODYyNjAyMzdfVjM)<br>![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=NTM2Yjc4ZGQ4MDYwMTIxZmViMmU5OTlmN2FlNDZlM2FfOWFkOWRiNzE3ZDg5ZjkxYzQ4ZWNkZjlkMjIxZjBiNGJfSUQ6NzY2Nzg1MjQ5NDIzMTg4MjY5OV8xNzg2MTczODM3OjE3ODYyNjAyMzdfVjM)<br><br>视频1:<br>\[439bdcb9c163\_02\_视频1\_J8LYbmp0yo\_6月5日\_\(4\)\(2\)\.mp4\]|<br>\[多模态参考新1\.mp4\]|
|- 保持视频1中的建筑、行人和整体环境为真实世界风格不变。仅将视频1画面中的树木、轿车转化为 3D 像素或体素积木风格 \(Minecraft style\)，风格参考图1。像素化物体的运动轨迹需正常，且保留真实环境的阴影和透射光。整体效果参考视频2。<br>|图1                                                       <br>![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=MWE3YjViNmJkZDQwZjI4NDQ4YTI3NTRkYTA0YjA2MjVfMGM0OTBkMTU1N2NhY2EzZTE2YzU4Yjk0MTI3YmQ3NjVfSUQ6NzY2Nzg1MjQ5MzEzNzE4NTc0OV8xNzg2MTczODM3OjE3ODYyNjAyMzdfVjM)<br>视频1                                       视频2<br>\[替换1\.1\.mp4\]<br><br>\[替换1\.mp4\]<br><br>|\[替换背景与特效1\.mp4\]<br>|
|- @图片1 镜头先快速推进到咖啡表面的奶泡、可可粉颗粒和深色咖啡液体纹理细节，让咖啡表面的颗粒、泡沫和液体涟漪逐渐覆盖全屏，遮挡住其他东西。镜头保持真实微距质感，极浅景深，细小粉末在逆光中缓慢飘落，表面纹理像细沙与流体之间的过渡。避免画面开裂，在咖啡粉颗粒、奶泡起伏、液体旋涡与@图片2 中沙丘沙脊、风蚀纹理、扬沙颗粒高度相似的瞬间，自然无痕转化为沙漠地貌，然后镜头继续向前推进，展示出@图片2 的沙丘全貌。严格避免画面开裂，不要黑屏，不要硬切，不要明显特效，不要拼接感，整体真实、安静、克制，像同一种颗粒材质从咖啡微观表面自然变成宏观沙漠世界。一镜到底，中间不要出现拼接。|图1                                   图2<br>![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=YmU1ZGMxNDliODU0ZTU5NzM1NzU3ZmI0MDljZDEyMjVfZGMwNTMxZjE1NzkzZTY5MDEyN2NkZTM3NGYwMDE4ZTRfSUQ6NzY2Nzg1MjQ5NDk3MzkxNDA0M18xNzg2MTczODM4OjE3ODYyNjAyMzhfVjM)<br><br>![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=YWEwNGE4ZDFhNTQ4ZGJjM2U2ZjU2N2ZlYjk1ZmVjMGVfOTZhYjY5Y2VjYTIxYjQ3Y2ZiOTgxNGY3NTY2YmI3MWJfSUQ6NzY2Nzg1MjQ5MTg3OTM4NjMwMF8xNzg2MTczODM4OjE3ODYyNjAyMzhfVjM)<br><br>|<br>\[全能参考新3\.mp4\]|

### 角**色、动作与镜头参考**

|提示词|输入文件|输出文件||
|---|---|---|---|
|- 角色动作融合参考<br>- 图1的人物动作、表情与表演节奏严格参考输入视频1<br>男生站在画面中右侧的水槽前把洗好的盘子递给画面左侧的女生，随后转身突然用右手向画面左侧边缘的女生甩出洗洁精泡沫。女生受到惊吓后立刻反击，两人开始开心地互相向对方泼洒泡沫并闪躲，伴随着大笑<br>|图1:<br>![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=OTk1YmJjOTg5Y2E5MjQwNWJjOTUxZDFiNzg5NmYxOTVfYzhhMDQ5YjhjNGU4MDkzZTA0OTdkMTkzZTNjNzg0ODZfSUQ6NzY2Nzg1MjQ5MzI4NDAzNTc3OF8xNzg2MTczODM3OjE3ODYyNjAyMzdfVjM)<br><br>视频1:<br>\[ref1\.mov\]|<br><br>\[角色替换\+动作参考\.mp4\]<br>真人感强，泡沫/场景提升真实度和细节，<br>两人互动生动||
|- 动作参考<br>- 人物参考视频1的动作，表演街舞，人物参考图1 图2<br>|图1图2:<br>![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=ODIzZmQ1ZjRlNWMxZjQ4NTk5OGE4ZDM2NzIzMjY2NjFfOGZiYzRkY2VjNGRiMmFhNjQ0ODMzMTg1ODBkOTMwMThfSUQ6NzY2Nzg1MjQ5MjUzNzY5NTE3NF8xNzg2MTczODM4OjE3ODYyNjAyMzhfVjM)<br><br><br>![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=OWNhNjFiYTkyNTkzNzU1Njk1NDdhYjk4ZDhlMGFjMWVfMzk4NzM1NTU0NzYwN2Y1NGY2ZTBkNTA3ZTJmZjhlZmFfSUQ6NzY2Nzg1MjQ5MzUzNTkwNjc3NF8xNzg2MTczODM4OjE3ODYyNjAyMzhfVjM)<br>视频1:<br>\[d9060f5cb9ab\_02\_视频1\_HDvmbpQrEo\_街舞3\.mp4\]<br>|\[角色替换\+动作参考2\.mp4\]<br>||
|- 运镜参考<br>- 提示词：参考视频1的希区柯克镜头运动，让视频2中的人物唱歌，歌声和唱歌表演参考视频3<br>|视频1<br>视频3<br>\[442949d9395a\_00\_视频1\_F22DbwP3ao\_6月5日\_\(2\)\.mp4\]<br>\[ae8eaa82fd3b\_01\_视频3\_EAFDbuLh9o\_6月5日\_\(4\)\.mp4\]<br>视频2<br>\[8479f915bc36\_02\_视频2\_P9hBbo99Qo\_6月5日\_\(4\)\(1\)\.mp4\]<br>|<br>\[60ba42e4d7b2\_denoise\_ids\_0\_final\.mp4\]|https://arena\-test\.xaminim\.com/?case\_id=2337|
|- 动作参考，DIY表情包<br>- 参考视频1进行动作模仿。固定机位全景镜头，正视频中三个穿西装的男人替换为三只高度写实的水豚。水豚必须严格遵循原视频的运动轨迹：依次迅速趴到地板上，然后最左边的水豚跳到中间位置，中间位置的水豚翻滚到最左边，接着中间的水豚翻滚到最右边，最右边的水豚跳跃到中间，最后中间水豚跳跃到另外两只背上，堆叠成金字塔形状。保持原有的固定机位不变。确保水豚的毛发质感和光影与环境融合|视频1<br>\[8b09f404c905\_01\_视频1\_Awwvb8zRjo\_6月8日\.mp4\]<br>|\[33a073d2c132\_denoise\_ids\_0\_final\.mp4\]<br>||



### **音色克隆与迁移**

|提示词|输入文件|输出文件|
|---|---|---|
|- 角色说话：Follow the wind, live free\.Leave worries behind, enjoy the moment，音色参考音频1<br>|<br>\[f463d523c5ce\_01\_音频1\_RSLcbpzJPo\_6月5日\(1\)\.mp3\]<br>\[297573323635\_00\_视频1\_YnyRbxEwio\_video\_20260525\_163755\_1927e9d3\.mp4\]|<br>\[音色克隆1\.mp4\]|



## **全能精准编辑与修改  **

H3支持多种维度的编辑与修改。角色替换、动作参考、背景替换、背景特效、台词替换与氛围感理解，并支持高精度的指令遵循能力。

通过精细化的控制，能更准确地落实创作者对画面、声音和节奏的修改需求，让内容调整更稳定、更可控。

- **角色与物体编辑：** 替换、删除或增加人物与物体，灵活调整画面主体

- **场景与视觉效果编辑：** 替换背景、调整光影氛围，并增加或修改视觉特效

- **声音、台词与音色修改：** 替换台词、迁移音色、调整人声及相关声音内容

- **高精度指令控制：** 准确执行局部修改与细化要求，同时保持未编辑内容相对稳定

### **角色与物体编辑**

|提示词Prompt|输入文件|输出文件|
|---|---|---|
|- 把视频中的猫换成狗<br>|\[15f67a0aaaad\_00\_参考视频\_Oa48bdWz8o\_Hailuo\_Video\_视频缓缓环绕，男子慢慢靠近猫，轻吻猫\_516340189738905608\.mp4\]<br>|\[角色替换3\.mp4\]|
|- 画面左边增加一个穿着相同团队制服的人，动作与旁人保持一致<br>|\[8f07c028de9f\_00\_参考视频\_U5dKbIbRNo\_Hailuo\_Video\_两个人缓缓往前走，有点失重的感觉\_516342590747250698\.mp4\]<br>|\[人物增加1\.mp4\]|
|**精准换人物与细节**<br>- 视频1中最后面的小孩换成 图1中的金毛狗， 视频1中最左边小孩穿的卡其色外套改成图2中的牛仔外套<br>|图1\+2:<br>![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=M2Q0YmQ3ZjU3NzNjNTg4MDU0ZDgyNzE4YjQyZTRmODVfYThmZDE3ZWNjOTIyZTBjOWIwNDM3OTQxNjg2ZjE5YWNfSUQ6NzY2Nzg1MjQ5NjQ1NTI0MDk4Nl8xNzg2MTczODM3OjE3ODYyNjAyMzdfVjM)<br><br>![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=M2NhYzk3MmNmY2U5ODU2MTBlYTRiNDIyNmEyMDYyMjBfZjRkNjZlYWNlNjJiMTQ3NTY1OWQwYTFiMTYwY2IyMDBfSUQ6NzY2Nzg1MjQ5NjY4NTg3ODQ3NV8xNzg2MTczODM3OjE3ODYyNjAyMzdfVjM)<br><br>参考视频：<br>\[5a9f2654e5b7\_02\_视频1\_Gs8EbpIi5o\_video\_20260526\_115007\_19d46168\_\(2\)\.mp4\]|\[角色替换1\.mp4\]<br>|





### **场景与视觉效果编辑**

|提示词Prompt|输入文件|输出文件|
|---|---|---|
|- 将视频1绿幕背景去除，变成类似视频2的童话感背景，背景元素需要完全匹配视频1的人物动作。修改视频1的人物光线，使之完全匹配背景。<br>|视频1:<br>\[34fc0be96d70\_00\_视频1\_Mp8ybNSuBo\_greenscreen\_original\_alice\_girl\_wave\_10s\.mp4\]<br>视频2:<br>\[Ref\.mov\]|<br>\[背景替换2\.mp4\]|
|- 替换光影<br>- 参考视频，改变光照，改成夜晚 <br>|\[dec8d155c7f3\_00\_参考视频\_HoePbE6pUo\_video\_20260525\_151209\_5e2b76f2 \(1\)\.mp4\]<br>|\[全能编辑\-光影1\.mp4\]<br>|
|- 实拍景色替换<br>视频1窗外的场景改成图1<br>|图1                  视频1<br>![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=Yzc2YzQ0YjNlYjk3MTI0MjVmZjE0NWE1NjE5YzgyZDdfYzJkMTUzZjgwYjlkYzdhMDQ1ODc3NmIwOTg4NWQyOTFfSUQ6NzY2Nzg1MjQ5NjIxNzY4OTM1NF8xNzg2MTczODM4OjE3ODYyNjAyMzhfVjM)<br><br>\[272821588752\_01\_视频1\_RKDCbrFoZo\_6月5日\_\(1\)\.mp4\]<br><br>|\[替换背景（实拍）1\.mp4\]<br>|



### **声音、台词与音色修改**

|提示词Prompt|输入文件|输出文件|
|---|---|---|
|- 将视频1女生说的话：“我们之间不可能在一起的，不是不爱，是我们真的走不到最后的”。改成音频1的台词：“别走了，好吗？这一次，我们不要放开彼此”，并略微调整对应的表演<br>|音频1:<br>\[e55d97d3d71e\_01\_FJnvbiLRao\_pleading\-reconciliation\.mp3\]<br><br>视频1:<br>\[aa101c18a06d\_00\_RHVTb5TOWo\_\_E9\_9B\_A8\_E5\_A4\_9C\_E7\_A6\_BB\_E5\_88\_AB\.mp4\]<br>|<br>\[音频替换1\.mp4\]|



### **高精度的指令遵循**

|提示词Prompt|输入文件|输出文件|
|---|---|---|
|- 将参考视频中的报纸替换为一本绿色封皮的书；人物所坐的椅子改为红色沙发；去掉人物佩戴的墨镜，保留清晰面部；移除汽车燃烧效果，使车辆保持正常状态；人物从怀里拿出的照片改为一个黑色小本子；同时在画面左侧增加一棵树<br>|视频1:<br>\[2650515f2106\_00\_参考视频\_VVu2bKK9Ko\_video\_20260529\_192640\_b02c3d2c\.mp4\]<br>|\[ec38ec963dff\_denoise\_ids\_0\_final\.mp4\]<br>|
|- 参考视频，将视频开头出现的易拉罐饮料替换为可口可乐；背景中原本发光的“全家”便利店招牌修改为“互惠”招牌；视频结尾塑料袋中的所有零食也统一替换为可口可乐易拉罐，最后结尾人物的台词从“买了一些小零食”变成了“买了一堆可乐”|视频1:<br>\[d3ffa21f26fa\_00\_参考视频\_JsoJbGI9Vo\_seedance2\-1780052267763\.mp4\]|\[高精度指令2\.mp4\]|
|- 两位魔术师站在舞台上面向观众表演"互换"魔术： 两人同时挥动魔杖，一阵烟雾升起。烟雾散去后，两人的西装颜色互换——左边的人穿白色西装，右边的人现在穿黑色西装，但两人手套颜色不变。 两人鞠躬致谢，身后的红色幕布拉上，从深红色渐变为深蓝色|![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=Mzk1MTBiNjU4NTI5NTNjODNiZmUwYTY0YWI3NGE0YjhfYjc5ZTdjMjdmYzJjNDUwYTcyYWFmNjcxNTI0NmRhNDBfSUQ6NzY2Nzg1MjQ5ODQwODk4Mzc1N18xNzg2MTczODM4OjE3ODYyNjAyMzhfVjM)<br>|\[精准参考魔术师\.mp4\]<br>|
|- 创意理解\+文字特效<br>- 在视频1中两个人周围加上图片1 这种橙黄色的手绘涂鸦，随着视频1中两人靠近，手绘涂鸦越来越多，从小的火花变成很明亮的光芒，在视频1中两个人亲吻时，手绘涂鸦出现粉红色的笔触<br>|图片1      <br>![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=OGY4NjhhMGQxMzY5NGU3OGM5MThhZDc1NmFhNWIyMzZfMGEwZGVhMjZmZTJlODdjNmUyMjcwOGQ5MDg4NTI4MzZfSUQ6NzY2Nzg1MjQ5NTUxMTUzODg5OF8xNzg2MTczODM3OjE3ODYyNjAyMzdfVjM)<br>视频1<br>\[4d5f71faace4\_00\_视频1\_X2UOb44HPo\_100794\-video\-720\.mp4\]|\[多维度参考3\.mp4\]<br>|



# **四、如何更好地使用 H3**

## **撰写提示词的友好建议：**

> 掌握提示词撰写技巧，在 MiniMax H3 生成你想要的视频。
> 
> 

### 整体公式

```Plain Text
**完整提示词 = 参考素材说明 + 核心创意 + 画面过程说明**
```

### 四个要素如何描述

|**参考素材说明**|告诉 H3 你上传的每个素材是干什么用的。<br>- **写清素材编号**：按你上传的顺序，比如@图片1，@音频2，@视频3<br>- **写清每个素材的用途**：人物参考（锁定脸/形象）/物体参考（锁定物体） / 场景参考（锁定场景）/关键帧（锁定帧，如果有首帧尾帧需求明确提出） / 音色参考（锁定音色）/故事版（根据故事版分镜生成镜头内容）/风格参考（根据图片的风格，生成类似的风格内容）/构图参考（根据图片中物体构图，生成对应的构图）/音频复用（生成视频的音频直接复用参考音频素材）/音频部分复用（生成视频某个声音轨道/某个时间段部分复用参考音频素材） / 动作参考（锁定动作）/运镜参考（锁定运镜）/视频编辑（对视频某个内容进行增删改），以及其他要求也可按需写明。<br>- **没有上传素材时整段跳过**<br>**示例**：<br>> @图片1 提供了xx角色的形象（如果有多个角色，需要能指代清楚），@视频2提供了动作参考。<br>> <br>> <br><br>如果素材中有非常想要保持的特征，建议明确写出来，这样可以让一致性更好。<br>在音频复刻/部分复刻中，如果对于人声对白内容/唱歌歌词内容的保持有较高的要求，强烈建议补充具体歌词文本内容。<br>> 比如@音频1 作为目标视频的音频复刻素材，具体歌词是：“ABCDEFGHIJKLMN”。<br>> <br>> |
|---|---|
|**核心创意**<br>|用一句话锁定全片信息，必须包含：<br>- **主体**：谁/什么（人/物/动物/其他）<br>- **地点**：在哪里<br>- **事件**：在做什么<br>- **题材/风格**：什么调性（写实/动画/电影感/广告片/纪录片……）<br>    - 特殊风格列举：<br>        - 赛博朋克/霓虹灯美学/涂鸦风 等<br>- **特殊运镜**：要不要特殊镜头（航拍/一镜到底/慢动作……）<br>    - 默认会切镜<br>    - 运镜风格<br>        > 写清即可；注意环绕运镜，建议用truck left\+pan right 或者 truck right\+pan left，而非直接说环绕运镜 <br>        > <br>        > <br>    - 切镜风格<br>        - 普通切镜（cut）<br>        - 叠化切镜（fade）<br>        - 随着节奏卡点切镜<br>        - 快切<br>- 如果任何元素有直接和引用素材的关联，都欢迎用户用@图片1/@音频1/@视频1等等方式强调下。 <br>**示例**：<br>> 一位穿汉服的年轻女子（@图片1）在樱花纷飞的庭院里舞剑，古典国风，电影质感，一镜到底。<br>> <br>> |
|**画面过程说明**<br>|按时间轴或故事线分段写，每个分镜/时间段包含两部分：<br>- **想要**（画面里要出现什么）：画面景别\+内容 \+ 运镜 \+ 动作 \+ 台词 \+ 音效<br>    - 以切镜shot作为时间戳的分段。每个shot内部写好景别，具体内容，shot内部运镜，人物台词，音效等这个shot内的内容<br>        - 注意台词的长短尽量和镜头长短对齐 （这个得强调下，很多口型问题会来自于这个）<br>        - 如果一句台词跨shot，可以用接着上个shot继续说这样的描述表明是跨shot的台词对白 <br>    - 如果任何元素有直接和引用素材的关联，**可用@图片1，@音频1 **等等方式强调下。<br>    - 如果你希望视频中出现具体文字、Logo、标题、标语、按钮文案等，一定要把文字原文写出来。<br>        例如：<br>        > *画面中出现英文 ：“H3”。*<br>        > <br>        > <br>        或者：<br>        > *手机屏幕上显示标题：“AI Video Creation”，按钮文字为：“Start Now”。*<br>        > <br>        > <br>- **不想要**（视频里不要出现什么）<br>    - 不想要背景音乐时，需明确写明，比如<br>        - 不希望视频里出现背景音乐，建议在提示词最后明确写：<br>        > *非叙事性音乐：N/A*<br>        > <br>        > <br>        或者使用英文格式：<br>        > *"non\_diegetic\_music": N/A*<br>        > <br>        > <br>        不要额外添加背景音乐。<br>- 尽量少写比喻句，多写看得见的画面<br>> 写 H3 提示词时，建议尽量使用具体、直接、可视化的描述，少写需要“意会”的句子。<br>> <br>> 因为 H3 更擅长理解明确的画面指令，而不是抽象比喻。<br>> <br>> <br>- 如有台词，必须明确具体内容，比如<br>> 一位穿汉服的年轻女子说：“你来了，剑等你好久了。”<br>> <br>> <br><br>**示例（需要再调整下例子）**：<br>> 0\-3 秒：全景，女子（@图片1）从画面左侧缓步走入樱花庭院（@图片2），背景虚化，没有对白，只有脚步声。<br>> 3\-8 秒：切镜到女子（@图片1）的中景，她拔出长剑（@图片3），缓缓起势，樱花瓣从树上飘落。镜头推进。<br>> 8\-12 秒：切镜到特写，剑光一闪，慢动作，樱花被剑气激得四散。<br>> 非叙事性音乐：N/A<br>> <br>> |

### 镜头怎么拆

> H3 有基础的分镜能力，以及 H3 对于切镜点遵从较强，如果你想要更好的生成，以下有一些建议：
> 
> 

- 台词：*台词的长短和画面变化内容需要合乎每个shot的长短逻辑，尽量不要出现一个3s shot说很大一段话的情况，会非常影响效果*

    - H3 能够响应跨shot （J\-cut，L\-cut）的台词响应，只要明确写出一句台词跨了哪些shot就可以响应！ 

    - 对于一个shot而言如果是画面内说话人角色，需写清楚是哪个角色说的，如果是画面外说话人，写清楚是画外说话人。如果发生了画内外因为切镜造成的转化的情况可以明确写出来，比如

    > 一个比较复杂的例子：
    > 
    > 一个画外音响起说：Wake up Wake up。之后切镜到一个中年妇女的近景，她是画外音的主人，她继续说道：It‘s time to go to school \! 
    > 
    > 

- 切镜一致性保持：

    - 切镜的时候可明确写出切镜到什么景别，具体主体是之前的哪个角色，有助于跨镜头一致性的保持 



### 三类模式生视频，提示词分别怎么写

|**上传多模态素材融合**<br>**（多模态参考）**|你可以同时上传：人物图 \+ 动作视频 \+ 场景图 \+ 音乐。**每个素材都要写清它的角色**：<br>- @图片1 → 人物参考（锁脸）<br>- @视频1 → 动作参考（锁动作）<br>- @音频1 → 节奏/情绪参考<br>**示例**：<br>> @图片1 是人物参考（锁这位女子的脸），@视频1 是动作参考（用里面的舞剑动作），@音频1 是情绪参考（古风配乐）。让这位女子在樱花庭院里按视频里的动作舞剑。<br>> <br>> |
|---|---|
|**上传图片生成视频**<br>**（图生视频）**|- **只上传 1 张图**：说清楚是**首帧**（视频开头画面）还是**尾帧**（视频结尾画面）<br>- **上传 2 张图（首\+尾帧）**：H3 不会自动加切镜，只补两帧之间的动作、光影、声音<br>**示例**：<br>> @图片1 是首帧参考图：女子持剑站在樱花树下。让她从持剑起势到舞剑完毕，自然衔接，不要切镜。<br>> <br>> |
|**纯文字生成视频**<br>|不依赖任何参考素材，直接根据你的文字提示词建立主体、场景、动作。<br>**这种模式**：<br>- 文字描述要**更具体**（主体外观、场景细节、动作描述都要写清）<br>- 多用「大全景交代空间 \+ 中景承载动作 \+ 特写强调细节」的分层写法<br>**示例**：<br>> 写实自然纪录片风格，电影级真实光影。清晨的薄雾中，在广阔的湿地芦苇荡里，一只优雅的白鹤单腿站立在浅水中，缓慢转头看向镜头。柔和的逆光，雾气在光束里飘动。<br>> <br>> |

### 容易踩的坑

|常见问题|怎么改|
|---|---|
|只写一段话没分段|按 3 段公式拆开写|
|素材上传了但没说用途|补一句「@图片1 是 XX 参考」|
|想用音乐但说「不要 BGM」|这两个矛盾，要么删一个，要么分场景写|
|想一镜到底但写了很多分镜|全文保持一段情节描述，删掉【镜头 N】结构|
|想要主角脸一致但没传图|一定要上传人物参考图，并标注「人物参考」|
|提示词太短（H3 没素材可参考时）|至少写出主体外观 \+ 场景细节 \+ 动作 \+ 风格|

## 

## 特定风格 · 提示词示意 

|**场景风格**|**完整提示词**|**参考**|**成片**|
|---|---|---|---|
|**大字幕 MV**|```Plain Text<br>【参考素材说明】@图片3：场景视觉风格（街道/夜间/地下空间、压迫感构图、环境层次、影像颗粒）@图片2：文字包装样式（字体质感、图形设计、动态图形排版冲击力）@图片1：人物形象（脸、发型、服装轮廓、比例、气质、整体氛围）只参考指定维度，不直接复制参考图，不出现真实品牌、原参考图 logo/标题/可识别文字。<br>【核心创意】10秒，16:9 横版 trap MV。两位 fly detective 兄弟搭挡在多个近景地下空间轮流对镜头 rap，全程跟随 trap 鼓点律动、卡点硬切，高反差印刷海报质感的英文块字随 bass hit 压屏出现。地下音乐录像带 + 时尚杂志拼贴 + 高时装质感，兄弟搭档式冷峻 performance。<br>【画面过程描述】Shot 1 — 面部极近特写 / 通道压迫感- 场景：狭窄通道或地下入口近景，参考 @图片3- 景别：面部极近特写（脸/眼神/肩颈/衣领局部）- 人物：Detective A 直视镜头开始 rap，眼神冷静锐利- 文字："TWO FLY" 巨大粗体英文压入画面上下，不遮挡眼睛- 律动：808 bass 砸下，"TWO FLY" 瞬间纵向压缩后回弹；hi-hat roll 时字母边缘高速细碎震动；"fly" 重音处扫描错位- 硬切Shot 2 — 中近景半身 / 墙面文字背景- 场景：另一处墙面/海报墙近景（和 Shot 1 空间明显不同）- 景别：明显拉到中近景半身- 人物：Detective B 对镜头 rap，肩膀和头部跟 hi-hat 点拍，身体轻微前倾- 文字："CLUES" 巨大压缩英文在人物身后，被头发/肩膀/服装轮廓自然遮挡- 律动：文字纵向拉伸如海报立起；每个 snare 时文字突然放大、抖动、扫描错位- 硬切Shot 3 — 手部特写 / 遮挡切换- 场景：金属门边/栏杆/车库墙面/低矮天花局部- 景别：手部近景（手/戒指/袖口/衣服材质为主体）- 人物：Detective A 手势向镜头推进（递线索），脸在后方虚化或局部- 文字：竖排 "BROTHERS" 在前景一侧，被手部短暂遮挡- 律动："move as one" 时文字被拉成一条长竖条，跟 bass hit 硬切重组- 硬切Shot 4 — 肩颈特写到面部特写 / 楼梯转角- 场景：楼梯转角/门口阴影/低矮通道- 景别：肩颈和衣领材质特写 → snare 时突然短促推近到面部特写- 人物：Detective B 侧头靠近镜头继续 rap- 文字："AS ONE" 像杂志标题被声音冲出来，在鼓点上突然放大- 律动：推近时文字位置硬切重排，始终不遮挡眼睛- 硬切Shot 5 — 半身近景残影 / 车库或混凝土背景- 场景：车库感空间或混凝土背景- 景别：Detective A 半身近景- 人物：主图层嘴型清楚同步，副图层动感残影（复印机错位/帧延迟，脸不变形），手势横向划过镜头- 文字：竖排 "CUT GOLD" 在背景跳帧闪现- 律动："CUT" 瞬间横向切开画面触发闪白硬切；"GOLD" 压缩成粗重块字后突然回弹- 硬切Shot 6 — 双人近景分屏 / 色块分割- 场景：地下入口/墙面/栏杆/门框（和 Shot 5 空间明显不同）- 景别：色块切成两/三区，两个 detective 面部特写和半身局部快速硬切交替- 人物：两 detective 在左右轮流表演- 文字：中央出现 "CASE COMPLETE" 粗体短词- 律动：随 808 bass hit 硬切重组，字母先压扁再瞬间拉伸；hi-hat roll 时文字碎片快速跳动；最后重音上出现扫描错位和纸张撕裂感震动- 硬切Final — 多场景近景 performance montage- 场景：狭窄通道面部特写、墙面中近景、手部特写、楼梯转角肩颈特写、车库半身局部、门口阴影双人近景快速交替- 景别：禁止全身、禁止多人全景，只用近景/中近景/面部特写/手部特写/肩颈特写/半身镜头- 人物：两位 detective 轮流对镜头 rap，嘴型/下颌/呼吸/眉眼/手势都精准卡住 vocal、snare、hi-hat roll、bass hit- 文字：最终主文字 "CASE CLOSED" 巨大压入画面- 律动：每次 bass hit 触发场景硬切或景别硬切；每次 snare 触发文字压屏或图层错位；最后一拍所有场景碎片同步冻结，hard cut to black<br>【整体要求补充】<br>▍影像风格（贯穿全片）- 粗颗粒、轻微胶片抖动、复印纸颗粒、半色调网点、印刷毛边、扫描错位、跳帧残影、高速图层错位- 剪辑节奏极快，只用硬切、跳切、鼓点切、遮挡切、闪白硬切、文字压屏硬切- 不用淡入淡出、不用柔和转场<br>▍文字包装（贯穿全片）- 文字是画面主体的一部分，有真实图层关系- 文字可出现在人物前景/中景/背景之间- 人物会遮挡文字，文字也可压过人物局部，但不能遮挡眼睛和主要面部表情- 文字跟随 vocal 重音、snare、hi-hat roll、808 bass hit 出现/震动/拉伸/压缩/错位/撕裂/硬切重组- 风格：粗重压缩无衬线、巨大英文块字、竖向拉伸、横向压缩、纵排英文、弧形标题、黑白红高反差、复印纸颗粒、半色调网点、印刷破损、扫描错位、zine 拼贴感- 文字数量克制：每镜头只 1 个主文字元素，最多少量编号；不要密集小字、不要 logo<br>▍律动规则（贯穿全片）- hi-hat roll → 快速微震、跳帧、文字细碎重组- snare → 文字猛然放大、画面硬切、人物肩膀下压- 808 bass hit → 低频压屏、画面短暂变形、文字纵向拉伸或横向压缩- vocal 关键词 → 嘴型同步、下颌动作、头部点拍、手势推进- 人物动作、文字动效、场景切换、景别切换必须共同卡点<br>▍场景切换（贯穿全片）- 多个近景场景快速硬切- 场景气质统一参考 @图片3，但每个镜头空间要明显不同：狭窄通道、墙面近景、门口阴影、金属/混凝土背景、灯光边缘、海报墙、楼梯转角、低矮天花、车库感空间、地下入口- 不做大远景，不做复杂大场面- 每次切换由 bass hit、snare、vocal 重音或文字压屏触发<br>▍景别切换（贯穿全片）- 变化要非常明显：面部极近特写 → 中近景半身 → 手部特写 → 肩颈特写 → 双人近景分屏 → 面部特写 → 半身局部- 不连续使用同一种景别- 每个硬切都让镜头距离/人物朝向/背景空间/文字层级产生明显变化- 镜头可轻微手持、突然推近、短促横移、快速压缩变焦、近距离摇摆- 不变成柔和慢镜头<br>▍人物规则（贯穿全片）- 角色：两位 fly detectives / brothers- 保持 @图片1 人物形象的脸、发型、服装轮廓、比例、气质、整体氛围- 真实哑光皮肤、干净高级、自然毛孔、轻微皮肤纹理- 不要油亮 AI 美颜脸- 兄弟搭档式轮流 rap，对镜头有强烈 performance<br>▍人物表演（贯穿全片）- 声音冷酷、攻击性、松弛但有压迫感，节奏紧、断裂、强拍- 不是静态摆拍，是在表演- 清楚嘴型同步：唇形、下颌、表情、呼吸跟随 vocal- 卡点动作：头部点拍、肩膀下压、手势推进、身体前倾、侧头、转身靠近镜头、手指指向镜头<br>▍重要限制（贯穿全片）- 不用全身镜头- 不用多人全景- 不用复杂群像大场面- 全片只用近景/中近景/面部特写/手部特写/肩颈特写/半身镜头- 只表现人物上半身、脸部、手势、衣服材质、表情、嘴型同步、文字包装- 不要求看到完整身体和脚- 不出现真实品牌、原参考图中的 logo、标题或可识别原文字<br>```|![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=ZTE1YTU3M2UxMjI2ZThlOWI0MjU5MWVmZTNjYzViOGZfY2EzMGNlZjIxOTUyNDg1ZDRmOWYxYmI0ZjA3MDJkNjdfSUQ6NzY2OTM5NzcwMzQ3Mzk0MTc3MV8xNzg2MTczODM4OjE3ODYyNjAyMzhfVjM)<br>![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=Yzc1OTkxMDI4MDE4ZDhmMjNlOTNiZjdhNmE0NjUwOWNfMTI3YzYxNTgxNjAyNGY5ZTA4OTk3OWQzZGMzZDE2ZTJfSUQ6NzY2OTM5NzcwMTMxMzg1ODQ5MV8xNzg2MTczODM3OjE3ODYyNjAyMzdfVjM)<br>![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=MzllMDdjZjUzNDZjODRlN2FmMjkxYzAzNDFiNTkyYWNfMTk5Y2RlYzQyOTliODI1NDUwNjExN2E3ZThkZGRkMzZfSUQ6NzY2OTM5NzcwMTQ2OTE0NjQwOF8xNzg2MTczODM3OjE3ODYyNjAyMzdfVjM)<br>|\[飞书20260730\-203458\.mp4\]<br>\[飞书20260730\-203504\.mp4\]<br>|
|**手绘特效**|```Plain Text<br>【参考素材说明】无参考素材（纯文字生成视频）。<br>【核心创意】15 秒，16:9 横版视频。将实拍的傍晚老式电车车厢与手绘发光动画融合：空荡末班电车车厢里，乘客用手机单手临时拍摄，遇到手绘杏橙色发光线在车厢里连续变形（车票→纸燕子→毛毛虫→箭头→小帆船→迷你电车→蜗牛→雨伞→小鱼→整车晚霞云海），最后回到车票碎成纸屑。整体生活感、怀旧、温柔而略带哀愁。<br>【画面过程描述】0〜3 秒- 正向：实拍镜头从拍摄者指尖在起雾车窗上随手画弧线开始。指尖离开，雾痕变成杏橙手绘发光线（蜡笔粉笔混合质感），先贴指尖→绕食指→落掌心卷成车票→被另一手按住→折成扁平纸燕子→沿右侧扶手环飞走。相机慢半拍追，先拍空掌和倒影，再匆忙右晃。- 反向：不要平稳广告式构图。3〜6 秒- 正向：纸燕子绕吊环飞一圈，尾巴勾住扶手环轻晃发出塑料碰撞声。拍摄者伸手想稳扶手环，纸燕子掠手背散成一串手绘逗号→首尾相连聚成发光毛毛虫→沿座椅靠背爬行（留杏橙粉末）→拍摄者弯腰看时拉直成涂鸦箭头→指完塌成小帆船沿座椅缝滑走。相机迟一步推进，运动模糊+短暂失焦。- 反向：不要新角色出现，所有形态必须首尾相连。6〜10 秒- 正向：小帆船滑地板、借电车晃动漂移、拖粉笔灰杏橙线→拍摄者伸脚挡+手捞→船从指鞋间溜过撞半卷车票→卷轴滚动→船被卷入又从另一侧钻出变成 2 节迷你手绘电车（车头保留船尖、车窗像毛毛虫点）→沿地板黑色缝线行驶→冲到路线图下车头一抬变扁平蜗牛（壳像车轮、身体拉长成车票线）→爬上金属立柱、回头抖触角催拍摄者追。- 反向：不要立体 CG。10〜13 秒- 正向：蜗牛触角碰车门按钮→按钮周围亮起杏橙手绘光圈→拍摄者想按→光圈弹开拉长蜗牛→变手绘小雨伞（伞面保留蜗牛壳螺旋和迷你电车窗点）→贴车门玻璃下滑、伞尖敲门缝（门缝街灯变成摇晃发光线）→伞翻面变带铃铛尾巴手绘鱼（鱼身如伞面、尾如车票虚线）→游到下方用尾巴扫拍摄者手腕（留下杏橙手环痕迹）→拍摄者后退撞座椅、镜头一歪再追车厢中央。- 反向：不要恐怖怪物化、不要扑咬。13〜15 秒- 正向：手绘鱼从车门玻璃散开→所有线迹沿窗玻璃、地板木纹、座椅缝、扶手环、路线图、天花板灯罩蔓延→整节车厢变巨大夕阳云海（窗铺晚霞、地板变发光小河、扶手环变圆月、路线图扩散成涂鸦小镇、天花板垂云带）→拍摄者后退伸手→空中云带落掌心变回车票→轻轻颤抖打喷嚏→满车厢晚霞线散成小纸屑→一片贴镜头边缘、另一只慢半拍小纸燕子从座椅缝钻出飞错方向笨拙掉到拍摄者手心→画面在温柔余韵中结束。- 反向：不要切镜到别的场景、不要凭空的恐怖元素。<br>【整体要求补充】<br>▍手绘动画风格（贯穿全片）- 始终是平面逐帧手绘发光涂鸦，不是立体角色或 CG 生物- 线条粗细、轮廓、填色每帧轻微变化，边缘有蜡笔/粉笔/彩色铅笔/粗糙笔刷/粉彩毛边- 涂色不均，有擦痕、颗粒、手工重画感- 中心色：杏橙、暖橘、淡奶白、少量柔和金- 发光柔和，只在玻璃/金属扶手/旧布座椅/木纹地板边缘留弱光晕，不强烈照亮实拍空间- 每次变形保留前一形态痕迹（雾痕弧线、车票虚线边、纸燕子翅膀、毛毛虫圆点、小帆船船头、迷你电车车窗、蜗牛壳螺旋、雨伞伞面、小鱼尾巴）—— 让观众感到是同一存在连续变形，不是新角色<br>▍相机节奏（贯穿全片）- 始终比手绘动画慢半拍- 动画先逃向扶手环/座椅缝/地板木纹/路线图/车门玻璃/车厢中央，相机再迟疑平移/低头/抬头/前进/后退追- 不提前构图，不让动画稳定居中，不平稳展示电车内饰- 保留：手持手机抖动、电车行驶摇晃、走路追赶的上下起伏、靠近玻璃的短暂失焦、窗外街灯曝光跳动、自然运动模糊- 像拍摄者真的在同一节车厢里一路追着它移动<br>▍禁止项（贯穿全片）- 禁止精密 3DCG、毛绒玩具风、三维渲染、平滑霓虹管、均匀矢量线、完成度过高的动态图形- 禁止电影感过强的布光、广告摄影式整洁构图、过度景深虚化- 禁止字幕、标志、背景音乐- 禁止突然切到别的场景- 禁止前形态消失后新角色凭空出现- 禁止巨大眼睛、裂嘴、牙齿、威吓、扑咬、突然黑屏、跳吓、恐怖怪物化- 最后的空间变形必须仍由手绘发光线条构成，可以奇妙梦幻不可思议，但保持温柔、怀旧、可爱、生活化、温柔而略带哀愁。<br>▍环境音（贯穿全片）- 只使用老式电车车厢内的真实声音：车轮与轨道的低沉摩擦声、车厢轻微摇晃声、扶手环碰撞声、车门按钮细小机械声、纸质车票摩擦声、布面座椅被碰到的声音、拍摄者小声惊呼和急促脚步声- 手绘动画声音：极轻的粉笔摩擦声、玻璃上滑动的细小刮擦声、柔软电子颤音、短促滑稽的鸣叫声<br>```|纯文生|\[海螺\_视频\_15秒，16\_9横版\_539178623442698249\.mp4\]<br>|



## **🐙撰写提示词的「最佳方式」**

> 把写提示词的任务交给专业的合作伙伴
> 
> 

如果你不想花大量时间研究提示词结构、镜头语言、素材引用方式和声音设计，也可以直接在 MiniMax Hub 里使用 H3 创作视频。

**MiniMax Hub是集合了「文本调研\+多媒体制作\+无限画布」的AI Agent 生产平台**

你不需要把每个镜头、景别、运镜、声音都写得非常专业，只需要用自然语言描述你的想法，

> 例如：“我想做一个雨夜追逐的电影感短片”或“帮我把这张人物图生成一段有情绪转折的视频”，
> 
> Agent 就会帮你理解创作意图，整理参考素材，补全镜头设计，优化提示词，并调动合适的生成能力完成视频创作。
> 
> 

相比自己反复摸索提示词，使用 MiniMax Hub 可以大大降低创作门槛，同时也能提升提示词的完整度和专业度，让 H3 更准确地理解主体、动作、镜头、节奏、声音和风格，从而显著提高视频生成质量。



**下载地址：**

- 国内版：https://hub\.minimaxi\.com/

- 海外版：https://hub\.minimax\.io/




# 四组画作的开放图像来源

核查日期为 2026-11-20。单位为馆内去重后的藏品或作品记录。各馆的分类、技法字段和图像权限标记不同，表内保留每项数值的实际口径。已经冻结的原尺度扩展沿用克利夫兰艺术博物馆的 60 件画作，本次馆藏核查用于判断独立补样来源。

## 分组口径

以[先导采集代码](../experiments/prepare_artworks.py)的技法和标题规则为起点。画布油画匹配 `oil on canvas`，木质基底油画匹配 `oil on panel`、`oil on wood` 或代码所列树种的单一木质基底。纸本水彩接受清楚标为水彩的作品及代码所列石墨或铅笔底稿，其纸张不得标有复合基底。纸本水墨要求馆方归为 Painting/Paintings，媒介明确为墨和纸。目录字段中的装裱前缀按先导规则处理，装裱、开本及裁片合格性需在纳入时核对。版画、书法、拆分画面和木制功能器物按标题、分类或媒介描述排除。若馆方提供像素尺寸，则另计短边至少 640 像素且长短边比不超过 2.8 的记录。

## 克利夫兰艺术博物馆

按现有代码的查询组合访问 `/api/artworks/`，设 `cc0=1`、`has_image=1`，每页 150，查到总数或 `skip=450` 页为止。为估计储备，本次跑满此上限，不使用采集脚本达到画家数量后提前停止的逻辑。用 `get_candidate` 复核逐件 `share_license_status=CC0`、作者、技法、标题及已记录的损伤描述、图像域名和馆方公布的尺寸，排除 `cma-121867` 后按入藏号去重。[馆方开放 API](https://www.clevelandart.org/open-access-api)

| 组别 | 搜索命中及读取数 | 通过先导元数据筛查 | 具名作者 |
|---|---|---:|---:|
| 画布油画 | Painting / `oil on canvas`，读 600 / 677 | 431 | 309 |
| 木质基底油画 | Painting / `oil on wood`，读 169 / 169，`oil on panel`，读 76 / 76 | 126 | 102 |
| 纸本水彩 | Drawing / `watercolor`，读 436 / 436，Painting / `watercolor`，读 3 / 3 | 41 | 30 |
| 纸本水墨 | Painting / `ink on paper`，读 600 / 1829 | 80 | 53 |

原始搜索会匹配含混合媒介和长卷等目录记录。画布油画和纸本水墨的查询未读完馆方命中。通过筛查的件数是可进一步查看的候选，已入实验的 15 件每组另有冻结清单及所用图像的校验。

## 大都会艺术博物馆

对固定 `MetObjects.csv` 使用 `Is Public Domain=True`，采用 `Classification` 的首段和 `Medium` 筛选，并按 `Object ID` 去重。水彩允许 Paintings 和 Drawings 类。逐组将所得编号按数值升序，读取前 25 个对象 API 响应，复核 `isPublicDomain=true` 与非空 `primaryImage`。馆方采用 CC0 发布其开放的公有领域作品图像。[固定目录快照](https://github.com/metmuseum/openaccess/tree/15d35b4b1f7f87baa8d42cc24481f68f76817d20) · [对象 API 文档](https://metmuseum.github.io/) · [馆方图像开放政策](https://www.metmuseum.org/hubs/open-access)

| 证据口径 | 画布油画 | 木质基底油画 | 纸本水彩 | 纸本水墨 |
|---|---:|---:|---:|---:|
| 快照中公共领域旗标与分组均匹配 | 1180 | 500 | 80 | 290 |
| 前 25 件核实开放主图链接 | 25 | 5 | 25 | 25 |

木质基底组另 20 次对象请求返回 HTTP 403。主图核验停留在对象 API，未读取实际图像尺寸。前 25 件按编号抽查，不能用它们的通过率推算全馆，纸本水彩的这批样本仅有三种作者标签。

## 美国国家美术馆（NGA）

对固定快照 `data/objects.csv` 保留入藏且非虚拟的记录，用 `classification`、`medium`、`title` 分组。以 `objectid = depictstmsobjectid` 连接 `data/published_images.csv`，要求 `viewtype=primary`、`openaccess=1` 与非空 `iiifurl`。结果按作品计数，尺寸来自已发布图像元数据。馆方的 `openaccess=1` 对应允许使用的开放图像，其开放图像政策以 CC0 发布。目录 CSV 自身也采用 CC0。[固定目录与图像元数据快照](https://github.com/NationalGalleryOfArt/opendata/tree/229b59876fa1c231c2fa72df4942ebc9b0737a54) · [字段字典](https://github.com/NationalGalleryOfArt/opendata/blob/229b59876fa1c231c2fa72df4942ebc9b0737a54/documentation/Data%20Dictionary.txt) · [馆方开放图像政策](https://www.nga.gov/terms-and-notices#open-access-policy-for-images-of-works-of-art-presumed-in-the-public-domain)

| 证据口径 | 画布油画 | 木质基底油画 | 纸本水彩 | 纸本水墨 |
|---|---:|---:|---:|---:|
| 目录中分类、标题与媒介匹配 | 2530 | 536 | 687 | 0 |
| 有馆方开放主图 | 1682 | 485 | 263 | 0 |
| 开放主图满足尺寸规则 | 1672 | 468 | 260 | 0 |

媒介文本另有 36 条符合单一墨纸规则的 Drawing 记录（查标题前），未计入纸本水墨绘画组。水彩类未并入 Index of American Design 的目录复制件。

## 芝加哥艺术博物馆（AIC）

逐条流式读取馆方全量 API 导出的 `json/artworks/*.json`。快照的 `Last-Modified` 为 2026-10-18 06:38:28 UTC，压缩包 SHA-256 为 `632d9b8796015c577ca54120a5466a8cd916ad24ff522b2650a9ef29573f7892`。共读 139,752 件，59,063 件同时标 `is_public_domain=true` 且有 `image_id`。用 `artwork_type_title`、`medium_display` 和 `title` 做组别筛选，水彩接受 `Painting`、`Drawing and Watercolor`。馆方建议使用标为 Public Domain 的藏品图像，并将符合开放条件的图像以 CC0 发布。`image_id` 关联馆方 IIIF 图像，尺寸来自 `thumbnail.width`、`thumbnail.height`。API 分页测试遇到 HTTP 403，以下数字来自完整快照。[馆方数据导出](https://github.com/art-institute-of-chicago/api-data#where-is-the-full-dataset) · [馆方 API 文档](https://api.artic.edu/docs/) · [馆方对 CC0 图像的说明](https://mw19.mwconf.org/glami/art-institute-of-chicago-website-redesign/index.html)

| 证据口径 | 画布油画 | 木质基底油画 | 纸本水彩 | 纸本水墨 |
|---|---:|---:|---:|---:|
| 公共领域旗标、主图 ID 与分组匹配 | 818 | 243 | 118 | 59 |
| 馆方图像尺寸满足规则 | 809 | 238 | 115 | 35 |

## 荷兰国立博物馆（Rijksmuseum）

在 `/search/collection` 使用组合参数和 `imageAvailable=true`，记录 `partOf.totalItems`。逐组检查首 20 个不同对象的 `?_profile=edm` 记录，要求 `ore:Aggregation` 提供 `edm:isShownBy` 与许可 `edm:rights`。馆方允许有 Public Domain Mark（PDM）或 CC0 标记的资源自由使用，其他图像的条款按每件标记判断。PDM 和 CC0 在记录中分别保留。[馆方搜索 API](https://data.rijksmuseum.nl/tutorials/search/) · [馆方开放政策](https://data.rijksmuseum.nl/policy) · [EDM 主图与权利标记示例](https://data.rijksmuseum.nl/200100988?_profile=edm)

| 组别 | 查询参数（均附 `imageAvailable=true`） | 目录命中 | 首 20 个主图为 PDM / CC0 / In Copyright |
|---|---|---:|---:|
| 画布油画 | `type=painting&material=oil+paint&material=canvas` | 2275 | 19 / 0 / 1 |
| 木质基底油画 | `type=schilderij&material=olieverf&material=paneel` | 1791 | 20 / 0 / 0 |
| 纸本水彩 | `technique=aquarelleren&material=papier` | 179 | 14 / 0 / 6 |
| 纸本水墨 | `type=painting&material=ink&material=paper` | 64 | 20 / 0 / 0 |

关键词查询会纳入复合媒介或非绘画类型。首 20 件中，再核对 EDM 类型与材料词表，两组油画纯媒介与 PDM 的交集分别为 19 和 20。水彩 PDM 样本中仅 1 件同时为纸和水彩且带 `drawing` 类型，另带 `postcard` 标签。纸墨 PDM 样本中 8 件材料仅为纸和墨且标有 `painting`。这些数未核对尺寸、画面边界和保存状态。其他检索写法中，木质油画采用 `material=wood` 得 81 件，水彩采用 `type=aquarel&material=papier` 得 3273 件，查询范围有潜在重叠，不相加。英语水彩技法词未命中，馆方 API 说明英语术语只覆盖部分词表。[语言和参数说明](https://data.rijksmuseum.nl/tutorials/search/#step-2--explore-the-available-parameters)

## 史密森尼学会（Smithsonian）

使用 Open Access API `/openaccess/api/v1.0/search`，检索共同条件为 `media_usage:"CC0" AND online_media_type:"Images"`。前三组允许 `object_type:(Paintings OR Drawings)` 以收集水彩，逐件筛选时油画仍仅用 Paintings。纸本水墨从检索环节限定 `object_type:"Paintings"`。对每组默认排序的首 100 条逐件读取 `freetext.physicalDescription` 的 `Medium`、`Materials` 或 `Material`，复核对象类别和媒介规则。只计有 `type=Images`、`usage.access=CC0` 且有图像链接的媒体，按馆内 `unitCode` 和 `record_ID` 去重。尺寸要求可由至少一个符合 CC0 的媒体条目满足。Smithsonian 的 CC0 元数据和 CC0 图像分别标记。[官方 API 与字段入口](https://github.com/Smithsonian/smithsonian-openaccess) · [馆方开放许可 FAQ](https://www.si.edu/openaccess/faq)

| 组别 | 额外关键词 | 目录命中 | 前 100 件中媒介匹配且有 CC0 图像 | 前 100 件中该 CC0 图像满足尺寸规则 |
|---|---|---:|---:|---:|
| 画布油画 | `"oil on canvas"` | 2553 | 82 | 80 |
| 木质基底油画 | `("oil on panel" OR "oil on wood" OR "oil on oak" OR "oil on poplar")` | 217 | 90 | 90 |
| 纸本水彩 | `((watercolor OR watercolour) AND paper)` | 3917 | 47 | 47 |
| 纸本水墨 | `"ink on paper"` | 171 | 92 | 87 |

API 搜索总数是全文命中，媒介、类型与许可的交集需读取逐件记录。一个藏品可有多个部位或视角的媒体。特别是长卷，能找到满足尺寸的 CC0 媒体还需核对它是否展示了预定的画面部分。

## 对实验取样的含义

当前 Cleveland 先导已从四组各冻结 15 件。单馆延续可避免在该轮同时改变采集来源。若需要独立补样，AIC 和 Smithsonian 的四组都得到至少 15 条有图像许可依据和尺寸证据的候选。NGA 的候选主要覆盖前面三组。Met 与 Rijksmuseum 可继续按对象找补充来源。

跨馆件数不合计。目录并未验证作品是否完好、是否同一件作品的另一版扫描、是否能够从绘画本体抽出合格的 512 像素裁片，或能否保持同样的作者控制。实际抽样仍需记录每件的许可与图像 URL，核对文件尺寸、画面边界与作品独立性。此次只取元数据和主图链接，未批量下载候选图像。以上统计不能用于估计 ARTeFACT 真实破损供体数量。

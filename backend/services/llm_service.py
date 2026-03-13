import os
import base64
from typing import Optional, List, Dict
from pathlib import Path
from dashscope import Generation


class LLMService:
    """大模型调用服务（支持多模态）"""

    def __init__(self, api_key: str, model_name: str = "qwen-vl-plus"):
        self.api_key = api_key
        self.model_name = model_name

        # 设置 API key
        os.environ["DASHSCOPE_API_KEY"] = api_key

    def _extract_images_from_markdown(self, markdown_content: str, task_id: Optional[str] = None) -> List[Dict]:
        """
        从 Markdown 内容中提取图片信息

        Args:
            markdown_content: Markdown 内容
            task_id: 任务 ID（如果有）

        Returns:
            图片信息列表，每个元素包含路径和 base64 编码
        """
        images = []

        # 简单的图片路径提取（匹配 ![](images/xxx.jpg) 格式）
        import re
        pattern = r'!\[\]\(images/([^)]+)\)'
        matches = re.findall(pattern, markdown_content)

        for image_name in matches:
            image_path = Path("./temp/mineru_output") / task_id / "auto" / "images" / image_name

            if image_path.exists():
                try:
                    with open(image_path, 'rb') as f:
                        image_base64 = base64.b64encode(f.read()).decode('utf-8')

                    images.append({
                        'name': image_name,
                        'base64': image_base64,
                        'path': str(image_path)
                    })
                except Exception as e:
                    print(f"读取图片失败 {image_name}: {e}")

        return images

    def _extract_image_filenames(self, markdown_content: str) -> str:
        """
        提取 Markdown 中的图片文件名列表

        Args:
            markdown_content: Markdown 内容

        Returns:
            图片文件名列表（字符串格式）
        """
        import re
        pattern = r'!\[\]\(images/([^)]+)\)'
        matches = re.findall(pattern, markdown_content)

        if matches:
            return "\n".join([f"- {img}" for img in matches])
        return "（无图片）"

    def _build_multimodal_message(self, markdown_content: str, images: List[Dict]) -> List[Dict]:
        """
        构建多模态消息（包含文本和图片）

        Args:
            markdown_content: Markdown 内容
            images: 图片信息列表

        Returns:
            消息列表
        """
        content = []

        # 添加文本内容
        prompt = f"""你是一个专业的学术论文分析助手。请仔细阅读提供的论文内容（包含文本和图片），生成结构化的学术笔记。

**必须严格按照以下结构生成笔记（使用 Markdown 格式）：**

## 论文基本信息
- **论文标题**：[论文标题]
- **作者**：[作者列表]
- **发表会议/期刊**：[会议或期刊名称]
- **发表年份**：[年份]

## 问题定义
[清晰定义论文要解决的核心问题是什么，研究背景和意义]

## 动机（Why）
[解释为什么需要解决这个问题，现有方法的不足之处，研究的必要性]

## 核心方法（How）
[详细描述论文提出的方法，包括：
- 方法框架和核心思想
- 关键算法和技术细节
- 系统架构和工作流程
- 与现有方法的区别]
- **重要：在适当位置插入相关的架构图**，使用格式 `![](images/图片文件名)`

## 关键技术/创新点
[列出论文的主要贡献和创新点，使用无序列表：
- 创新点1
- 创新点2
- ...]

## 实验设置 & 结果
[总结实验设计和主要结果：
- 实验数据集
- 对比方法
- 评估指标
- 主要实验结果和性能提升
- **重要：在描述图表时，插入对应的图片**，使用格式 `![](images/图片文件名)`

## 优点 / 局限
[客观评价论文：
**优点：**
- 优点1
- 优点2

**局限：**
- 局限1
- 局限2]

## 我的疑问 / 想法
[这部分留空，供读者自己填写]

**核心要求：**
1. **仔细阅读并理解每一张图片**：图片可能包含架构图、表格、公式、图表等重要信息
2. **必须在生成的笔记中保留所有图片引用**：在适当的位置使用 `![](images/图片文件名)` 格式插入图片
3. 在笔记中详细描述图片的内容和含义
4. 对于架构图，说明组件之间的关系和数据流
5. 对于表格，总结关键数据和趋势
6. 对于公式，解释其含义和应用场景
7. 专业、简洁、学术化的表达风格
8. 重要概念、定义使用**加粗**标记
9. 使用无序列表、有序列表组织要点
10. 保持学术严谨性，避免使用表情符号
11. 确保每个部分都有实质内容，不要省略任何一个章节

原始文档中包含的图片文件名如下（请务必在生成的笔记中使用这些图片）：
{self._extract_image_filenames(markdown_content)}

文档内容如下：
{markdown_content}

请生成符合上述结构的专业学术笔记（Markdown 格式，包含对图片的详细分析和图片引用）："""

        # 构建多模态消息：先添加文本，再添加所有图片
        content.append({'text': prompt})

        # 添加图片（使用 base64 data URL 格式）
        for img in images:
            # 检测图片类型
            image_name = img['name'].lower()
            if image_name.endswith('.jpg') or image_name.endswith('.jpeg'):
                mime_type = 'image/jpeg'
            elif image_name.endswith('.png'):
                mime_type = 'image/png'
            elif image_name.endswith('.gif'):
                mime_type = 'image/gif'
            elif image_name.endswith('.webp'):
                mime_type = 'image/webp'
            else:
                mime_type = 'image/jpeg'  # 默认

            # 使用 base64 data URL 格式
            content.append({
                'image': f"data:{mime_type};base64,{img['base64']}"
            })

        return content

    def _build_simple_prompt(self, pdf_content: str) -> str:
        """
        构建简单提示词（不包含图片）

        Args:
            pdf_content: PDF 解析后的 Markdown 内容

        Returns:
            完整的提示词
        """
        prompt = f"""你是一个专业的学术论文分析助手。请仔细阅读提供的论文内容，生成结构化的学术笔记。

**必须严格按照以下结构生成笔记（使用 Markdown 格式）：**

## 论文基本信息
- **论文标题**：[论文标题]
- **作者**：[作者列表]
- **发表会议/期刊**：[会议或期刊名称]
- **发表年份**：[年份]

## 问题定义
[清晰定义论文要解决的核心问题是什么，研究背景和意义]

## 动机（Why）
[解释为什么需要解决这个问题，现有方法的不足之处，研究的必要性]

## 核心方法（How）
[详细描述论文提出的方法，包括：
- 方法框架和核心思想
- 关键算法和技术细节
- 系统架构和工作流程
- 与现有方法的区别]

## 关键技术/创新点
[列出论文的主要贡献和创新点，使用无序列表]

## 实验设置 & 结果
[总结实验设计和主要结果]

## 优点 / 局限
[客观评价论文的优缺点]

## 我的疑问 / 想法
[这部分留空，供读者自己填写]

**核心要求：**
1. 专业、简洁、学术化的表达风格
2. 重要概念、定义使用**加粗**标记
3. 使用无序列表、有序列表组织要点
4. 保持学术严谨性，避免使用表情符号
5. 确保每个部分都有实质内容，不要省略任何一个章节

文档内容：
{pdf_content}

请生成符合上述结构的专业学术笔记（Markdown 格式）："""
        return prompt

    async def generate_notes(self, pdf_content: str, task_id: Optional[str] = None, temperature: float = 0.7) -> dict:
        """
        生成笔记（支持多模态）

        Args:
            pdf_content: PDF 解析后的 Markdown 内容
            task_id: 任务 ID（用于提取图片）
            temperature: 温度参数，控制随机性

        Returns:
            生成的笔记和元数据
        """
        try:
            # 提取图片
            images = []
            if task_id:
                images = self._extract_images_from_markdown(pdf_content, task_id)

            # 限制图片数量（通义千问 VL 模型最多支持 10 张图片）
            MAX_IMAGES = 10
            if len(images) > MAX_IMAGES:
                print(f"Warning: Found {len(images)} images, but only first {MAX_IMAGES} will be used")
                images = images[:MAX_IMAGES]

            # 构建消息
            if images:
                # 多模态调用
                messages = [{
                    'role': 'user',
                    'content': self._build_multimodal_message(pdf_content, images)
                }]

                print(f"使用多模态模型，包含 {len(images)} 张图片")

                # 调用通义千问多模态 API
                response = Generation.call(
                    model=self.model_name,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=4000,
                    result_format='message'
                )
            else:
                # 纯文本调用
                prompt = self._build_simple_prompt(pdf_content)
                messages = [{'role': 'user', 'content': prompt}]

                print("使用纯文本模式")

                response = Generation.call(
                    model=self.model_name,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=4000,
                    result_format='message'
                )

            # 打印响应用于调试
            print(f"API 响应状态码: {response.status_code}")
            print(f"API 响应类型: {type(response)}")

            # 如果状态码不是 200，打印详细错误信息
            if response.status_code != 200:
                print(f"错误详情:")
                if hasattr(response, 'message'):
                    print(f"  message: {response.message}")
                if hasattr(response, 'code'):
                    print(f"  code: {response.code}")
                if hasattr(response, 'request_id'):
                    print(f"  request_id: {response.request_id}")
                # 打印完整的响应对象用于调试
                print(f"  完整响应: {response}")

            # 检查响应状态
            if response.status_code == 200:
                # 尝试不同的响应格式
                try:
                    # 尝试新格式（多模态）
                    if hasattr(response, 'output') and response.output:
                        if hasattr(response.output, 'choices') and response.output.choices:
                            notes = response.output.choices[0].message.content
                        else:
                            # 可能直接是 content
                            notes = response.output.content if hasattr(response.output, 'content') else str(response.output)
                    else:
                        # 尝试旧格式
                        notes = response.output.choices[0].message.content

                except (AttributeError, IndexError, KeyError) as e:
                    print(f"解析响应失败，尝试备用方法: {e}")
                    print(f"响应对象: {dir(response)}")
                    if hasattr(response, 'output'):
                        print(f"output 对象: {dir(response.output)}")
                    # 最后的备用方案
                    notes = str(response)

                return {
                    "status": "success",
                    "notes": notes,
                    "model": self.model_name,
                    "tokens_used": response.usage.total_tokens if hasattr(response, 'usage') and response.usage else 0
                }
            else:
                return {
                    "status": "error",
                    "error": f"API 调用失败: {response.message if hasattr(response, 'message') else '未知错误'}",
                    "code": response.status_code
                }

        except Exception as e:
            import traceback
            print(f"生成笔记时发生异常:\n{traceback.format_exc()}")
            return {
                "status": "error",
                "error": f"生成笔记时发生错误: {str(e)}"
            }

    async def generate_notes_stream(self, pdf_content: str, task_id: Optional[str] = None, temperature: float = 0.7):
        """
        流式生成笔记（支持多模态）

        Args:
            pdf_content: PDF 解析后的 Markdown 内容
            task_id: 任务 ID（用于提取图片）
            temperature: 温度参数

        Yields:
            生成的文本片段
        """
        try:
            # 提取图片
            images = []
            if task_id:
                images = self._extract_images_from_markdown(pdf_content, task_id)

            # 限制图片数量（通义千问 VL 模型最多支持 10 张图片）
            MAX_IMAGES = 10
            if len(images) > MAX_IMAGES:
                print(f"Warning: Found {len(images)} images, but only first {MAX_IMAGES} will be used")
                images = images[:MAX_IMAGES]

            # 构建消息
            if images:
                messages = [{
                    'role': 'user',
                    'content': self._build_multimodal_message(pdf_content, images)
                }]
                print(f"流式输出：使用多模态模型，包含 {len(images)} 张图片")
            else:
                prompt = self._build_simple_prompt(pdf_content)
                messages = [{'role': 'user', 'content': prompt}]
                print("流式输出：使用纯文本模式")

            # 调用通义千问 API（流式）
            response = Generation.call(
                model=self.model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=4000,
                stream=True,
            )

            for chunk in response:
                if chunk.status_code == 200:
                    yield chunk.output.choices[0].message.content
                else:
                    yield f"\n\n错误: {chunk.message}"
                    break

        except Exception as e:
            yield f"\n\n错误: {str(e)}"

    async def generate_ppt_content(self, notes: str, task_id: Optional[str] = None, temperature: float = 0.7) -> dict:
        """
        基于笔记生成适合 PPT 展示的内容

        Args:
            notes: LLM 生成的笔记内容
            task_id: 任务 ID（用于提取图片）
            temperature: 温度参数

        Returns:
            生成的 PPT 内容和元数据
        """
        try:
            # 提取图片（如果笔记中包含图片引用）
            images = []
            if task_id:
                images = self._extract_images_from_markdown(notes, task_id)

            # 构建 PPT 内容生成的提示词
            prompt = f"""你是一个专业的 PPT 内容设计师。请基于提供的学术笔记，生成适合 PowerPoint 演示文稿展示的内容。

**必须严格按照以下结构生成（使用 Markdown 格式）：**

# PPT标题
[论文标题 - 简洁版]

## 作者信息
[作者1, 作者2, ...]

## 目录
1. 问题定义
2. 研究动机
3. 核心方法
4. 关键创新
5. 实验结果
6. 总结评价

## 第1页：问题定义
**标题**：研究背景与核心问题
**要点**：
- 要点1
- 要点2
- 要点3
（每页3-5个要点，每个要点不超过20字）

## 第2页：研究动机
**标题**：为什么需要这项研究
**要点**：
- 要点1
- 要点2
- 要点3

## 第3页：核心方法（上）
**标题**：方法框架概述
**要点**：
- 要点1
- 要点2
- 要点3
**图片**：![](images/xxx.jpg)（如果有架构图）

## 第4页：核心方法（下）
**标题**：关键技术创新
**要点**：
- 要点1
- 要点2
- 要点3

## 第5页：关键创新点
**标题**：主要贡献
**要点**：
- 创新点1
- 创新点2
- 创新点3

## 第6页：实验设置
**标题**：实验设计
**要点**：
- 数据集
- 对比方法
- 评估指标

## 第7页：实验结果
**标题**：主要实验结果
**要点**：
- 结果1
- 结果2
- 结果3
**图片**：![](images/xxx.jpg)（如果有结果图）

## 第8页：总结评价
**标题**：优点与局限
**要点**：
- 优点1
- 优点2
- 局限1
- 局限2

## 第9页：启发思考
**标题**：我的思考
**要点**：
- 可以借鉴的地方
- 可能的改进方向
- 应用场景

**核心要求：**
1. 每页标题简洁明了（不超过15个字）
2. 每页3-5个要点，每个要点精炼（不超过20个字）
3. 要点使用无序列表格式（- 开头）
4. 保留笔记中的重要图片引用，使用 ![](images/xxx) 格式
5. 内容要适合演讲展示，简洁有力
6. 避免长段落，全部使用要点形式
7. 总页数控制在10-15页

基于以下学术笔记生成 PPT 内容：

{notes}

请生成符合上述结构的 PPT 内容（Markdown 格式）："""

            # 构建消息
            if images:
                # 多模态调用

                messages = [{
                    'role': 'user',
                    'content': self._build_multimodal_message(notes, images)
                }]

                # 替换 prompt 为 PPT 专用 prompt
                messages[0]['content'][0]['text'] = prompt

                print(f"生成 PPT 内容：使用多模态模型，包含 {len(images)} 张图片")

                # 调用通义千问多模态 API
                response = Generation.call(
                    model=self.model_name,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=4000,
                    result_format='message'
                )
            else:
                # 纯文本调用
                messages = [{'role': 'user', 'content': prompt}]

                print("生成 PPT 内容：使用纯文本模式")

                response = Generation.call(
                    model=self.model_name,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=4000,
                    result_format='message'
                )

            # 检查响应状态
            if response.status_code == 200:
                try:
                    # 尝试新格式（多模态）
                    if hasattr(response, 'output') and response.output:
                        if hasattr(response.output, 'choices') and response.output.choices:
                            ppt_content = response.output.choices[0].message.content
                        else:
                            ppt_content = response.output.content if hasattr(response.output, 'content') else str(response.output)
                    else:
                        ppt_content = response.output.choices[0].message.content

                except (AttributeError, IndexError, KeyError) as e:
                    print(f"解析响应失败: {e}")
                    ppt_content = str(response)

                return {
                    "status": "success",
                    "ppt_content": ppt_content,
                    "model": self.model_name,
                    "tokens_used": response.usage.total_tokens if hasattr(response, 'usage') and response.usage else 0
                }
            else:
                return {
                    "status": "error",
                    "error": f"API 调用失败: {response.message if hasattr(response, 'message') else '未知错误'}",
                    "code": response.status_code
                }

        except Exception as e:
            import traceback
            print(f"生成 PPT 内容时发生异常:\n{traceback.format_exc()}")
            return {
                "status": "error",
                "error": f"生成 PPT 内容时发生错误: {str(e)}"
            }

    async def generate_marp_content(self, pdf_content: str, task_id: Optional[str] = None, temperature: float = 0.7) -> dict:
        """
        基于论文内容生成适合 Marp 的 Markdown 内容

        Args:
            pdf_content: PDF 解析后的 Markdown 内容
            task_id: 任务 ID（用于提取图片）
            temperature: 温度参数

        Returns:
            生成的 Marp Markdown 内容和元数据
        """
        try:
            # 提取图片（如果笔记中包含图片引用）
            images = []
            if task_id:
                images = self._extract_images_from_markdown(pdf_content, task_id)

            # 构建 Marp 内容生成的提示词
            prompt = f"""# Role
你是一个专业的学术演讲PPT制作专家，擅长将论文转换为清晰、简洁、视觉化的PPT大纲。

# Task
将提供的论文内容转换为适合制作PPT的Markdown格式。

# Output Format
使用 Marp 格式（Markdown Presentation），每页幻灯片用 `---` 分隔。

# Content Guidelines

1. **详细描述要点**
   - 每页4-6个要点
   - 每个要点15-30个字
   - 保留重要细节和解释
   - 提供充分的技术细节

2. **结构化**
   - 用项目符号 `-` 列表
   - 使用嵌套列表展示层次关系
   - 保持平行结构
   - 重要概念使用**粗体**

3. **视觉化（最高优先级）**
   - **必须包含所有图片**：使用 `![](images/图片文件名)` 或 `<img src="images/图片文件名" style="..." />` 格式
   - **必须包含所有公式**：使用 `$$...$$` LaTeX格式
   - **必须包含所有表格**：使用Markdown表格语法
   - 关键词用**粗体**
   - 每页内容要充实，不要留白太多

4. **分页原则**
   - 一页一个主题，但内容要详细
   - 每页包含充分的细节说明
   - 相关内容可以合并展示
   - 避免过于简略的要点

# Slide Structure (10-15 slides，每页内容充实)

1. 标题页
2. Abstract/Motivation（详细描述）
3. Background（详细说明背景知识）
4. Related Work（全面综述）
5. Method Overview（方法概述）
6. Method Details（详细方法，包含公式页面，2-3页）
7. Experiments & Results（实验和结果，包含表格页面，2-3页）
8. Conclusion（总结贡献）
9. Q&A

# 重要：必须提取公式和表格

**必须主动查找并提取论文中的所有公式和表格，不能遗漏！**

1. **公式提取要求**：
   - 仔细扫描论文中所有的数学公式
   - 识别关键公式、算法、计算方法
   - 将每个重要公式转换为单独的幻灯片页面
   - 使用 `$$...$$` LaTeX格式
   - 公式居中显示，用 `<div style="text-align: center;">` 包裹
   - 附带3个要点的详细解释

2. **表格提取要求**：
   - 仔细扫描论文中所有的表格
   - 识别实验结果、对比分析、参数设置等表格
   - 将每个重要表格转换为单独的幻灯片页面
   - 使用Markdown表格语法
   - 表格居中显示，用 `<div style="text-align: center;">` 包裹
   - 突出最佳结果（使用**粗体**）
   - 附带3个要点的数据分析

3. **公式/表格页面插入位置**：
   - 公式：在解释方法细节的页面之后插入
   - 表格：在实验结果部分插入
   - 不要把公式和表格混在其他内容中

# 必须使用的样式配置（直接复制，不要添加代码块标记）

---
marp: true
theme: gaia
paginate: true
style: |
  section {{
    font-size: 20px;
    font-family: 'Microsoft YaHei', 'SimHei', Arial, sans-serif;
    line-height: 1.4;
    padding: 30px;
  }}
  h1 {{
    font-size: 28px;
    color: #1976d2;
    border-bottom: 2px solid #1976d2;
    padding-bottom: 8px;
    margin-bottom: 18px;
    font-weight: 600;
  }}
  h2 {{
    font-size: 22px;
    color: #2c3e50;
    margin-top: 15px;
    font-weight: 600;
  }}
  h3 {{
    font-size: 19px;
    color: #1976d2;
    font-weight: 600;
  }}
  strong {{
    color: #1976d2;
    font-weight: 600;
  }}
  ul {{
    line-height: 1.6;
    margin-top: 10px;
  }}
  li {{
    margin-bottom: 6px;
  }}
  table {{
    font-size: 14px;
    border-collapse: collapse;
    width: 100%;
    margin: 12px auto;
    display: table;
    margin-left: auto;
    margin-right: auto;
  }}
  th {{
    background: #1976d2;
    color: white;
    padding: 6px 10px;
    font-weight: 600;
  }}
  td {{
    border: 1px solid #ddd;
    padding: 6px 10px;
    text-align: center;
  }}
  tr:nth-child(even) {{
    background: #f5f5f5;
  }}
  img {{
    max-height: 300px;
    width: auto;
    object-fit: contain;
    display: block;
    margin: 0 auto;
  }}
  .katex-display {{
    margin: 20px auto;
    text-align: center;
  }}
---

# Example Format

# 论文标题

**作者**
单位

---

# 页面标题

## 要点1
- 关键点
- 关键点

## 要点2
- 关键点
- 关键点

---

# 双栏布局

<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 2rem;">

<div>

### 左侧
- 内容

</div>

<div>

### 右侧
- 内容

</div>

</div>

---

# 公式页

$$
公式内容
$$

## 说明
- 符号含义
- 关键洞察

---

# 表格页

| 指标 | 方法1 | 方法2 | **Ours** |
|------|-------|-------|---------|
| 指标1 | 值1 | 值2 | **最佳值** |
| 指标2 | 值3 | 值4 | **最佳值** |

**关键发现**：
- 发现1
- 发现2

# 图片页面（图片居中，下方简明说明）

## 图片主题

<div style="text-align: center;">

<img src="images/图片文件名" style="width: 100%; max-height: 300px; object-fit: contain; display: block; margin: 0 auto;" />

**简明说明**（3-4个要点，每个要点25-40字）：
- 要点1：图中展示了系统的核心架构
- 要点2：各组件的交互关系清晰可见
- 要点3：关键创新点在图中得到体现

</div>

---

# 公式页面（公式居中，下方解释）

<div style="text-align: center;">

$$
公式内容（如：L = \\sum_{{i=1}}^{{n}} (y_i - \\hat{{y}}_i)^2）
$$

**公式说明**：
- 符号含义：L表示损失函数，n表示样本数量
- 公式作用：计算预测值与真实值的误差
- 关键洞察：该公式体现了优化的核心目标

</div>

---

# 表格页面（表格居中，下方分析）

<div style="text-align: center;">

| 指标 | 方法1 | 方法2 | **Ours** |
|------|-------|-------|---------|
| Accuracy | 85.2% | 88.7% | **92.3%** |
| Precision | 83.1% | 87.4% | **91.5%** |
| Recall | 84.6% | 88.1% | **92.0%** |

**关键发现**：
- 本方法在所有指标上均优于对比方法
- Accuracy提升3.6-7.1个百分点
- 验证了方法的有效性和稳定性

</div>

---

# Available Images

**重要**：论文中包含以下图片，你**必须**在生成的 PPT 中使用这些图片。为每个重要图片创建单独的幻灯片页面，使用图片居中布局。

{self._extract_image_filenames(pdf_content)}

# Image Usage Requirements

1. **必须使用所有相关图片** - 不要跳过任何图片
2. **每个图片单独一页** - 为重要的架构图、流程图、实验结果图等创建专门的幻灯片
3. **使用图片居中布局** - 图片在页面中央，使用 `<div style="text-align: center;">` 包裹
4. **简明描述图片内容**（3-4个要点即可，每个要点15-25字）：
   - **图表类型**：架构图/流程图/实验结果图/对比图/拓扑图等
   - **核心内容**：简要说明图片展示的主要内容
     - 图中的主要组件和要素
     - 组件之间的关系和交互
     - 数据流向和处理流程
     - 关键发现和结果
   - **关键洞察**：从图中提取的2-3个重要信息
5. **图片格式**：`<img src="images/图片文件名" style="width: 100%; max-height: 300px; object-fit: contain; display: block; margin: 0 auto;" />`
6. **图片大小**：最大高度300px，宽度自适应，居中显示
7. **文字说明要简洁** - 每个图片页的文字说明包含3-4个要点即可

# Formula & Table Requirements

1. **公式必须居中显示** - 使用 `<div style="text-align: center;">` 包裹公式和说明
2. **公式格式**：使用 `$$...$$` 包裹LaTeX公式
3. **公式说明**（3个要点）：
   - 符号含义：解释公式中的关键符号
   - 公式作用：说明公式的功能和目的
   - 关键洞察：公式体现的核心思想
4. **表格必须居中显示** - 使用 `<div style="text-align: center;">` 包裹表格和分析
5. **表格格式**：使用标准Markdown表格语法，突出最佳结果（使用**粗体**）
6. **表格分析**（3个要点）：
   - 对比结果：指出最优方法
   - 性能提升：具体的改进数据
   - 验证结论：说明结果的意义

# Input Paper
{pdf_content}

# 重要提示：在生成PPT前，先扫描论文内容

**请先执行以下扫描任务**：

1. **公式扫描**：在论文内容中查找所有数学表达式、公式、算法
   - 查找包含数学符号的段落（如：Σ、∫、∂、α、β等）
   - 查找公式标记（如：Equation、Formula、算法描述）
   - 查找计算方法、损失函数、优化目标等
   - **记录每个公式的位置和内容**

2. **表格扫描**：在论文内容中查找所有表格
   - 查找表格标记（如：Table、表格、Tab.）
   - 查找对比实验结果
   - 查找参数设置表
   - 查找性能评估表
   - **记录每个表格的位置和内容**

3. **组织结构规划**：
   - 为每个找到的重要公式规划一个独立的幻灯片页面
   - 为每个找到的重要表格规划一个独立的幻灯片页面
   - 在合适的位置插入这些页面

# Constraints

**核心原则（按优先级排序）**：

1. **【最高优先级】必须包含所有图片**
   - 这是硬性要求，不能跳过任何图片
   - 在论文内容中查找所有 `![](images/xxx.jpg)` 格式的图片引用
   - 为每个重要图片创建单独的幻灯片页面
   - 使用 `<img src="images/图片文件名" style="width: 100%; max-height: 300px; object-fit: contain; display: block; margin: 0 auto;" />` 格式
   - 图片必须居中显示，用 `<div style="text-align: center;">` 包裹
   - 图片说明要简洁（3-4个要点，每个15-25字）

2. **【第二优先级】必须包含所有公式**
   - 仔细扫描论文，找到所有数学公式（包括行内公式和独立公式）
   - 为每个重要公式创建单独的幻灯片页面或嵌入到相关页面中
   - 使用 `$$...$$` LaTeX格式
   - 公式必须居中显示，用 `<div style="text-align: center;">` 包裹
   - 附带3个要点的说明（符号含义、公式作用、关键洞察）

3. **【第三优先级】必须包含所有表格**
   - 仔细扫描论文，找到所有表格
   - 为每个重要表格创建单独的幻灯片页面或嵌入到相关页面中
   - 使用Markdown表格语法
   - 表格必须居中显示，用 `<div style="text-align: center;">` 包裹
   - 突出最佳结果（使用**粗体**）
   - 附带3个要点的分析（对比结果、性能提升、验证结论）

**其他要求**：
- 输出完整的 Markdown 文件
- 不要添加解释性文字
- 直接输出可用的 Markdown
- 每页内容要详细充实
- 每个要点必须详细描述，15-30个字
- 避免内容过于简略，每页都要有足够的技术细节

**质量检查清单**：
- ✓ 是否包含了所有图片？
- ✓ 是否包含了所有公式？
- ✓ 是否包含了所有表格？
- ✓ 图片、公式、表格是否都居中显示？
- ✓ 是否有清晰的解释说明？"""

            # 构建消息
            if images:
                # 多模态调用
                messages = [{
                    'role': 'user',
                    'content': self._build_multimodal_message(pdf_content, images)
                }]

                # 替换 prompt 为 Marp 专用 prompt
                messages[0]['content'][0]['text'] = prompt

                print(f"生成 Marp 内容：使用多模态模型，包含 {len(images)} 张图片")

                # 调用通义千问多模态 API
                response = Generation.call(
                    model=self.model_name,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=4000,
                    result_format='message'
                )
            else:
                # 纯文本调用
                messages = [{'role': 'user', 'content': prompt}]

                print("生成 Marp 内容：使用纯文本模式")

                response = Generation.call(
                    model=self.model_name,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=4000,
                    result_format='message'
                )

            # 检查响应状态
            if response.status_code == 200:
                try:
                    # 尝试新格式（多模态）
                    if hasattr(response, 'output') and response.output:
                        if hasattr(response.output, 'choices') and response.output.choices:
                            marp_content = response.output.choices[0].message.content
                        else:
                            marp_content = response.output.content if hasattr(response.output, 'content') else str(response.output)
                    else:
                        marp_content = response.output.choices[0].message.content

                    # 清理可能的代码块标记
                    if marp_content.strip().startswith('```'):
                        lines = marp_content.split('\n')
                        # 移除第一行的 ```markdown 或 ```
                        if lines[0].strip().startswith('```'):
                            lines = lines[1:]
                        # 移除最后一行的 ```
                        if lines[-1].strip() == '```':
                            lines = lines[:-1]
                        marp_content = '\n'.join(lines)
                        print("已清理代码块标记")

                except (AttributeError, IndexError, KeyError) as e:
                    print(f"解析响应失败: {e}")
                    marp_content = str(response)

                return {
                    "status": "success",
                    "marp_content": marp_content,
                    "model": self.model_name,
                    "tokens_used": response.usage.total_tokens if hasattr(response, 'usage') and response.usage else 0
                }
            else:
                return {
                    "status": "error",
                    "error": f"API 调用失败: {response.message if hasattr(response, 'message') else '未知错误'}",
                    "code": response.status_code
                }

        except Exception as e:
            import traceback
            print(f"生成 Marp 内容时发生异常:\n{traceback.format_exc()}")
            return {
                "status": "error",
                "error": f"生成 Marp 内容时发生错误: {str(e)}"
            }

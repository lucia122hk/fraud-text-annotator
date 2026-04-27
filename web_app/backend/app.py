from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import os
import sys
import requests
import time
from openai import OpenAI

app = Flask(__name__)
CORS(app)

# 16label标签映射
LABEL_MAPPING = {
    'G1': 'G1: Wealth Bait',
    'G2': 'G2: Relationship Bait',
    'G3': 'G3: Opportunity Bait',
    'L1': 'L1: Security Threat',
    'L2': 'L2: Property Threat',
    'L3': 'L3: Privacy Threat',
    'R1': 'R1: Relative Impersonation',
    'R2': 'R2: Authority Impersonation',
    'R3': 'R3: Customer Service Impersonation',
    'C1': 'C1: False Click',
    'C2': 'C2: False Input',
    'C3': 'C3: False Identification',
    'C4': 'C4: False Trigger',
    'C5': 'C5: Remote Control',
    'OT': 'OT: Other Fraud',
    'NS': 'NS: Insufficient Information'
}

def call_llm(api_key, api_url, model_name, prompt, text, idx=0):
    """调用LLM进行标注"""
    try:
        # 使用OpenAI客户端
        client = OpenAI(
            api_key=api_key,
            base_url=api_url
        )
        
        user_content = f"""样本ID：{idx}
文本：{text}
"""
        
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": user_content}
        ]
        
        response = client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=0.1,
            timeout=60
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        print(f"LLM调用失败: {e}")
        return None

def parse_llm_output(output):
    """解析LLM输出为二进制向量和时间序列标签"""
    import re
    
    if not output:
        return None, None
    
    vector = None
    time_series = "[]"
    
    # 尝试多种解析方式获取标签向量
    
    # 方式1：查找"标签向量："后面的内容
    vector_match = re.search(r'标签向量：([\d,\s]+)', output)
    if vector_match:
        vector_str = vector_match.group(1)
        numbers = re.findall(r'\d+', vector_str)
        try:
            vector = [int(num) for num in numbers if num in ['0', '1']]
            if len(vector) != 16:
                vector = None
        except:
            pass
    
    # 方式2：直接提取所有0和1的序列
    if not vector:
        numbers = re.findall(r'\d+', output)
        try:
            vector = [int(num) for num in numbers if num in ['0', '1']]
            if len(vector) != 16:
                vector = None
        except:
            pass
    
    # 方式3：查找包含16个数字的行
    if not vector:
        lines = output.split('\n')
        for line in lines:
            numbers = re.findall(r'\d+', line)
            try:
                vector = [int(num) for num in numbers if num in ['0', '1']]
                if len(vector) == 16:
                    break
                else:
                    vector = None
            except:
                pass
    
    # 解析时间序列标签
    time_series_match = re.search(r'时间序列：(\[.+?\])', output, re.DOTALL)
    if time_series_match:
        time_series = time_series_match.group(1)
    
    return vector, time_series

def annotate_16labels(text, config=None):
    """16label标注函数"""
    try:
        # 获取API配置
        if config:
            api_key = config.get('apiKey') or config.get('api_key')
            api_url = config.get('apiUrl') or config.get('api_url', 'https://dashscope.aliyuncs.com/compatible-mode/v1')
            model_name = config.get('modelName') or config.get('model_name', 'qwen-plus')
            annotation_prompt = config.get('annotationPrompt') or config.get('annotation_prompt')
        else:
            # 使用默认配置
            config_path = '/Users/warmirror/Documents/5508/multi_label_annotation_system/config.json'
            if os.path.exists(config_path):
                import json
                with open(config_path, 'r') as f:
                    cfg = json.load(f)
                    api_key = cfg.get('llm1_api_key')
                    api_url = cfg.get('llm1_api_url', 'https://dashscope.aliyuncs.com/compatible-mode/v1')
                    model_name = cfg.get('llm1_model', 'qwen-plus')
                    annotation_prompt = None
            else:
                return None, "请先配置API密钥"
        
        if not api_key:
            return None, "请先配置API密钥"
        
        # 系统提示词
        system_prompt = "你是严谨的诈骗分类标注助手，严格按规则判断每个标签是否存在（0=不存在，1=存在），输出简体中文，不主观发挥。"
        
        # 用户提示词
        if annotation_prompt:
            user_prompt = annotation_prompt.format(text=text, idx=1)
        else:
            user_prompt = f"""首先判断以下文本是否描述了诈骗行为(行为人虚构事实或隐瞒真相 + 受害方错误认识 + 主动处分财产,未遂也算。）若非诈骗，16标签项全部输出0。若为诈骗，首先判断是否信息不全，如果没有任何手法描述，判定为信息不足，第16个标签S填写1(此时通常前15项都为0)，否则填写0。若非信息不全，那么请根据以下文本，判断下列16个标签是否存在。标签顺序及定义如下：

1. G1 财富诱饵：承诺高回报、中奖、免费送、稳赚不赔等直接金钱利益。
2. G2 关系诱饵：以新建立的关系（如网友、新认识的恋人） 出现，承诺获利。
3. G3 机会诱饵：提供内部名额、高薪兼职、限量抢购等稀缺机会。
4. L1 安全诱饵：威胁账户异常、设备中毒、信息泄露等。
5. L2 财产诱饵：威胁欠费逾期、影响征信、法院传票、罚款等。
6. L3 隐私诱饵：威胁曝光私密视频、公开聊天记录、征信黑名单等。
7. R1 亲友冒充：冒充亲属、朋友、恋人。
8. R2 权威冒充：冒充公检法、政府机构、学校、公司领导。
9. R3 客服/平台冒充：冒充银行、电商、支付工具、运营商客服。
10. C1 误点击：伪装按钮、透明覆盖层、虚假关闭图标等。
11. C2 误输入：伪造登录/支付页面、虚假表单。
12. C3 误识别：SEO投毒、相似域名、仿冒APP图标。
13. C4 误触发：系统警报循环、倒计时压迫、虚假更新。
14. C5 远程控制：诱导安装远控软件、伪装技术支持。
15. OT 其他诈骗：有其他诈骗手段的明确信息但与前14项不同，该项填写1，否则填0。
16. NS 信息不全：有诈骗发生但缺失细节。

补充：利用新认识的关系承诺获利→ G2；冒充已知亲友进行后续诈骗→ R1

输出格式（严格按模板输出，不得改结构，标签顺序固定为G1,G2,G3,L1,L2,L3,R1,R2,R3,C1,C2,C3,C4,C5,OT,NS）：
---
样本ID：1
标签向量：0或1,0或1,0或1,0或1,0或1,0或1,0或1,0或1,0或1,0或1,0或1,0或1,0或1,0或1,0或1,0或1
判断依据(一句话)：
---

现在判断以下文本：
{text}""".format(text=text)
        

        
        # 调用LLM
        output = call_llm(api_key, api_url, model_name, system_prompt, user_prompt)
        
        if output:
            vector, time_series = parse_llm_output(output)
            if vector:
                results = {}
                labels = ['G1', 'G2', 'G3', 'L1', 'L2', 'L3', 'R1', 'R2', 'R3', 'C1', 'C2', 'C3', 'C4', 'C5', 'OT', 'NS']
                for i, label in enumerate(labels):
                    if i < len(vector):
                        results[LABEL_MAPPING.get(label, label)] = vector[i]
                return results, time_series, None
        
        return None, "[]", "标注失败"
        
    except Exception as e:
        return None, "[]", str(e)

def filter_glr(results):
    """筛选GLR三类混合型"""
    if not results:
        return {}
    
    glr_results = {}
    for label, value in results.items():
        if label.startswith('G1:') or label.startswith('G2:') or label.startswith('G3:') or \
           label.startswith('L1:') or label.startswith('L2:') or label.startswith('L3:') or \
           label.startswith('R1:') or label.startswith('R2:') or label.startswith('R3:'):
            glr_results[label] = value
    return glr_results

def generate_timeline_label(glr_results):
    """时序标签打标"""
    if not glr_results:
        return "无欺诈"
    
    g_count = sum(1 for label, value in glr_results.items() if (label.startswith('G1:') or label.startswith('G2:') or label.startswith('G3:')) and value == 1)
    l_count = sum(1 for label, value in glr_results.items() if (label.startswith('L1:') or label.startswith('L2:') or label.startswith('L3:')) and value == 1)
    r_count = sum(1 for label, value in glr_results.items() if (label.startswith('R1:') or label.startswith('R2:') or label.startswith('R3:')) and value == 1)
    
    total_glr = g_count + l_count + r_count
    
    if total_glr >= 2:
        if g_count > 0 and l_count > 0 and r_count > 0:
            return "GLR复合型欺诈"
        elif g_count > 0 and l_count > 0:
            return "GL复合型欺诈"
        elif g_count > 0 and r_count > 0:
            return "GR复合型欺诈"
        elif l_count > 0 and r_count > 0:
            return "LR复合型欺诈"
        else:
            return "单一类别多子项欺诈"
    elif total_glr == 1:
        if g_count == 1:
            return "G类单一型欺诈"
        elif l_count == 1:
            return "L类单一型欺诈"
        elif r_count == 1:
            return "R类单一型欺诈"
        else:
            return "单一型欺诈"
    else:
        return "无欺诈"

def build_time_series_prompt(query, existing_labels, idx):
    """构建时间序列标签的prompt"""
    return f"""已知以下文本已被标注为包含下列标签（标签代码见末尾），请根据文本中这些手法出现的自然顺序，输出时间序列（只对已有标签排序）。

文本：{query}

已有标签：{existing_labels}

规则：

1.按手法在文本中出现的先后顺序排列，最早出现的排第一。例如 ["G1","R2"]

2.若两个手法在同一句话或同一个紧密耦合的表述中同时出现（如"我是公安局的，不转账就冻结账户"同时包含 R2 和 L2），用 & 连接，例如 ["R2 & L2", "G1"]。

3.若顺序无法判断（如信息不足或手法交错复杂），输出 ["unknown"]。

4.G1包括法律赔偿、退款、和解金等任何直接金钱利益，不限于"刷单返利"等简单表述。

5.顺序必须基于诈骗实施的自然流程，而不是报道中提及的顺序。比如冒充通常发生在利益承诺之前。

6.禁止重复与冗余：每个原始标签在时间序列中只能出现一次。如果一个标签已经被包含在 & 组合中（如 R2 & L2 已经包含了 R2 和 L2），则不能再单独列出该标签（即不能再输出单独的 "R2" 或 "L2"）。最终输出的序列中，所有 & 内外的原子标签去重后，必须与输入的已有标签集合完全相等，不能多也不能少。

标签代码解释：

- G1:财富诱饵，G2:关系诱饵，G3:机会诱饵

- L1:安全威胁，L2:财产威胁，L3:隐私威胁

- R1:亲友冒充，R2:权威冒充，R3:客服/平台冒充

输出格式（严格按模板，不得修改结构）：

---

时间序列：[]

OT描述：

---

请直接输出，不要添加任何额外解释。"""

def get_time_series_label(text, existing_labels, config=None):
    """获取时间序列标签"""
    try:
        # 获取API配置
        if config:
            api_key = config.get('apiKey') or config.get('api_key')
            api_url = config.get('apiUrl') or config.get('api_url', 'https://dashscope.aliyuncs.com/compatible-mode/v1')
            model_name = config.get('modelName') or config.get('model_name', 'qwen-plus')
        else:
            # 使用默认配置
            config_path = '/Users/warmirror/Documents/5508/multi_label_annotation_system/config.json'
            if os.path.exists(config_path):
                import json
                with open(config_path, 'r') as f:
                    cfg = json.load(f)
                    api_key = cfg.get('llm1_api_key')
                    api_url = cfg.get('llm1_api_url', 'https://dashscope.aliyuncs.com/compatible-mode/v1')
                    model_name = cfg.get('llm1_model', 'qwen-plus')
            else:
                return None, "请先配置API密钥"
        
        if not api_key:
            return None, "请先配置API密钥"
        
        # 构建prompt
        prompt = build_time_series_prompt(text, existing_labels, 1)
        
        # 调用LLM
        output = call_llm(api_key, api_url, model_name, "你是严谨的诈骗文本标注助手，严格按规则判断时间序列，输出简体中文，不主观发挥。", prompt)
        
        if output:
            # 解析时间序列
            import re
            time_series_match = re.search(r'时间序列：(\[.+?\])', output)
            if time_series_match:
                time_series = time_series_match.group(1)
                return time_series, None
        
        return None, "时间序列标注失败"
        
    except Exception as e:
        return None, str(e)

@app.route('/api/test', methods=['POST'])
def test_api():
    """测试API连接"""
    data = request.json
    config = data.get('config', {})
    
    api_key = config.get('apiKey') or config.get('api_key')
    api_url = config.get('apiUrl') or config.get('api_url', 'https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions')
    model_name = config.get('modelName') or config.get('model_name', 'qwen-plus')
    
    if not api_key:
        return jsonify({'error': '请输入API密钥'}), 400
    
    # 尝试调用API
    test_prompt = "你好"
    try:
        result = call_llm(api_key, api_url, model_name, test_prompt, "测试")
        if result:
            return jsonify({'status': 'success', 'message': 'API连接成功'})
        else:
            return jsonify({'error': 'API调用失败 - 未返回响应结果'}), 400
    except Exception as e:
        return jsonify({'error': f'API调用失败 - {str(e)}'}), 400

@app.route('/api/annotate', methods=['POST'])
def annotate_text():
    """单条文本标注"""
    data = request.json
    text = data.get('text', '')
    config = data.get('config', {})
    
    # 16label标注
    annotations, time_series, error = annotate_16labels(text, config)
    
    if error:
        return jsonify({'error': error}), 400
    
    # 筛选GLR
    glr_results = filter_glr(annotations)
    
    # 时序标签
    timeline_label = generate_timeline_label(glr_results)
    
    return jsonify({
        'text': text,
        'annotations': annotations,
        'time_series': time_series
    })

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """批量文件标注"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # 获取配置
    config_str = request.form.get('config', '{}')
    import json
    try:
        config = json.loads(config_str)
    except:
        config = {}
    
    # 保存文件
    file_path = os.path.join('/tmp', file.filename)
    file.save(file_path)
    
    # 缓存文件路径
    cache_file = os.path.join('/tmp', f"{file.filename}_cache.json")
    
    try:
        # 读取文件
        if file.filename.endswith('.csv'):
            df = pd.read_csv(file_path)
        elif file.filename.endswith('.xlsx'):
            df = pd.read_excel(file_path)
        else:
            return jsonify({'error': 'Unsupported file format'}), 400
        
        total = len(df)
        
        if total == 0:
            return jsonify({'error': '文件中没有数据'}), 400
        
        # 检查缓存文件
        results = []
        start_idx = 0
        
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cached_data = json.load(f)
                results = cached_data.get('results', [])
                start_idx = len(results)
                if start_idx > 0:
                    print(f"Resuming from index {start_idx}")
            except:
                pass
        
        # 处理每条文本
        for idx in range(start_idx, total):
            row = df.iloc[idx]
            text = str(row.iloc[0]) if len(row) > 0 else ''
            
            if not text or text == 'nan':
                continue
            
            # 16label标注
            annotations, time_series, error = annotate_16labels(text, config)
            
            if error:
                # 使用默认结果
                annotations = {label: 0 for label in LABEL_MAPPING.values()}
                time_series = "[]"
            
            # 筛选GLR
            glr_results = filter_glr(annotations)
            
            # 时序标签
            timeline_label = generate_timeline_label(glr_results)
            
            results.append({
                'text': text,
                'annotations': annotations,
                'time_series': time_series,
                'progress': {
                    'current': idx + 1,
                    'total': total,
                    'percent': int((idx + 1) / total * 100)
                }
            })
            
            # 每100条保存一次缓存
            if (idx + 1) % 100 == 0 or (idx + 1) == total:
                cache_data = {
                    'results': results,
                    'total': total,
                    'processed': idx + 1,
                    'timestamp': time.time()
                }
                with open(cache_file, 'w', encoding='utf-8') as f:
                    json.dump(cache_data, f, ensure_ascii=False, indent=2)
                print(f"Saved cache at index {idx + 1}")
        
        # 完成后删除缓存文件
        if os.path.exists(cache_file):
            os.remove(cache_file)
            print("Cache file removed after completion")
        
        return jsonify(results)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)
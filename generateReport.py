
import json
import time



def generateReport(srcthirty,srcfive,srcA,srcB,srcC,srcD,probA,probB,probC,probD,imprA,imprB,imprC,imprD,rewr,analysis,latter,grammar,passage,question_num,stamp=time.time(),current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time())),file_path='static/table/Record', annotation_json='[]'):
    def lattercolor(lat):
        if 0<=lat<=2:
            return 'green'
        elif 3<=lat<=7:
            return 'orange'
        else:
            return 'red'
        
    def grammarcolor(gra):
        if 0<=gra<=2:
            return 'green'
        elif 3<=gra<=7:
            return 'orange'
        else:
            return 'red'

    try:
        annotation_data = json.loads(annotation_json)
        if not isinstance(annotation_data, list):
            annotation_data = []
    except json.JSONDecodeError:
        annotation_data = []

    passage_json = json.dumps(passage, ensure_ascii=False)
    annotation_data_json = json.dumps(annotation_data, ensure_ascii=False)
    
    template =f'''
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://unpkg.com/tippy.js@6/dist/tippy.css">
    <script src="https://unpkg.com/@popperjs/core@2"></script>
    <script src="https://unpkg.com/tippy.js@6"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.7.2/css/all.min.css" rel="stylesheet">
    <title id='stamp'>Discussion Page {question_num}, {stamp}</title>
    <style>
        .annotated-essay {{
            line-height: 2.1;
            white-space: pre-wrap;
        }}
        .essay-mark {{
            border-bottom: 1px dotted #9ca3af;
            cursor: help;
            position: relative;
        }}
        .essay-mark::before {{
            content: "";
            width: 7px;
            height: 7px;
            border-radius: 9999px;
            position: absolute;
            top: -9px;
            left: 50%;
            transform: translateX(-50%);
            box-shadow: 0 0 0 2px #ffffff;
        }}
        .essay-mark.grammar::before {{
            background: #93c5fd;
        }}
        .essay-mark.spelling::before {{
            background: #f9a8d4;
        }}
        .essay-mark.wording::before {{
            background: #86efac;
        }}
        .issue-card {{
            max-width: 280px;
            font-size: 13px;
            line-height: 1.45;
        }}
        .issue-card strong {{
            display: block;
            margin-bottom: 4px;
        }}
    </style>
</head>
<body>
<div class="container mx-auto bg-white rounded-lg shadow-lg p-6" id="reportborder">
        <div >
            <h1 style="font-size: 45px;">Deepseek Evaluation Report</h1>
            <h1 style="font-size: 9px; color:rgb(156, 155, 155)" id="geninfo">GenerateTime: {current_time}             ·            Question: {question_num}</h1>
            <br/>
            
            <h3 style="color:gray; font-size: 18px;">> Total Score(5/30): </h3>
            <h2  id="src" style='font-size:40px; color:green'>{srcfive} / {srcthirty:.0f}</h2>
                        
            <br/>

            <h3 style="color:gray; font-size: 18px;">> Breakdown</h3>
            <div class="grid-container">
            <div class="item" style="color:gray"><center>Criteria</center></div>
            <div class="item" style="color:gray" ><center>Score</center></div>
            <div class="item">Content Relevance</div>
            <div class="item" id="srcA">{srcA}</div>
            <div class="item">Perspectives Expansion</div>
            <div class="item" id="srcB">{srcB}</div>
            <div class="item">Linguistic Expression</div>
            <div class="item" id="srcC">{srcC}</div>
            <div class="item">Logical structure</div>
            <div class="item" id="srcD">{srcD}</div>
            </div>
            

            
            <style>
            .grid-container {{
            display: grid;
            grid-template-columns: repeat(2, 1fr); 
            gap: 2px; 
            }}
            .item {{
            padding: 10px;
            background: #f0f0f0;
            }}
            </style>
                        
            <br/>

            <p style="font-size: 14px;">拼写错误数量：</p>
            <p style="font-size: 17px; color: {grammarcolor(int(grammar))}" id="grammar">{grammar}</p>
            <p style="font-size: 14px;">语法错误数量：</p>
            <p style="font-size: 17px; color: {lattercolor(int(latter))}" id="latter">{latter}</p>


            <h3 style="color:gray; font-size: 18px;">> Problem Analysis</h3>
            <p  id="probA"> - Content Relevence: {probA}</p>
            <p id="probB"> - Perspectives Expansion: {probB}</p>
            <p id="probC"> - Linguistic Expression: {probC}</p>
            <p id="probD"> - Logical structure: {probD}</p>
            <br/>

            <h3 style="color:gray; font-size: 18px;">> Improvements</h3>
            <p id="imprA"> - Content Relevence: {imprA}</p>
            <p id="imprB"> - Perspectives Expansion: {imprB}</p>
            <p id="imprC"> - Linguistic Expression: {imprC}</p>
            <p id="imprD"> - Logical structure: {imprD}</p>
                        
            <br/>

            <h3 style="color:gray; font-size: 18px;">> AI Rewrite</h3>
            <p id="rewr">{rewr}</p>

            <div style="display: none;">
            <h3 style="color:gray; font-size: 18px;">> Sentence-by-sentence linguistic analysis</h3>
            <p id="analysis">{analysis}</p>
            </div>

            <br/><br/>

            <h3 style="color:gray; font-size: 18px;">> Your Answer</h3>
            <p id="org" class="annotated-essay"></p>
            </div>
    </div>
    <script>
        function escapeHtml(value) {{
            return String(value).replace(/[&<>"']/g, (char) => ({{
                '&': '&amp;',
                '<': '&lt;',
                '>': '&gt;',
                '"': '&quot;',
                "'": '&#39;'
            }}[char]));
        }}

        function issueTypeLabel(type) {{
            return {{
                grammar: '语法问题',
                spelling: '词汇拼写问题',
                wording: '用词不当问题'
            }}[type] || '问题';
        }}

        function buildIssueCard(issue) {{
            return `<div class="issue-card">
                <strong>${{escapeHtml(issueTypeLabel(issue.type))}}</strong>
                <div>问题：${{escapeHtml(issue.problem || '未提供')}}</div>
                <div>改进：${{escapeHtml(issue.suggestion || '未提供')}}</div>
            </div>`;
        }}

        function renderAnnotatedEssay(text, annotations) {{
            const container = document.getElementById('org');
            const validAnnotations = Array.isArray(annotations)
                ? annotations.filter((item) => item && item.text && ['grammar', 'spelling', 'wording'].includes(item.type))
                : [];

            const ranges = [];
            let cursor = 0;
            validAnnotations.forEach((item) => {{
                let start = text.indexOf(item.text, cursor);
                if (start === -1) {{
                    start = text.indexOf(item.text);
                }}
                if (start === -1) {{
                    return;
                }}
                const end = start + item.text.length;
                const overlaps = ranges.some((range) => start < range.end && end > range.start);
                if (!overlaps) {{
                    ranges.push({{ start, end, item }});
                    cursor = end;
                }}
            }});

            ranges.sort((a, b) => a.start - b.start);
            let html = '';
            let position = 0;
            ranges.forEach((range) => {{
                html += escapeHtml(text.slice(position, range.start));
                html += `<span class="essay-mark ${{range.item.type}}" data-tippy-content="${{escapeHtml(buildIssueCard(range.item))}}">${{escapeHtml(text.slice(range.start, range.end))}}</span>`;
                position = range.end;
            }});
            html += escapeHtml(text.slice(position));
            container.innerHTML = html || escapeHtml(text);

            if (window.tippy) {{
                tippy('.essay-mark', {{
                    allowHTML: true,
                    placement: 'top',
                    interactive: true,
                    maxWidth: 320,
                    appendTo: document.body
                }});
            }}
        }}

        renderAnnotatedEssay({passage_json}, {annotation_data_json});
    </script>
    </body>
    </html>
'''
    filepath=file_path +f'/Discussion Page {question_num}, {stamp}.html'
    with open(filepath,'w',encoding='utf-8') as file:
        file.write(template)


    return filepath
    

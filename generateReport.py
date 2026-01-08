
import time



def generateReport(srcthirty,srcfive,srcA,srcB,srcC,srcD,probA,probB,probC,probD,imprA,imprB,imprC,imprD,rewr,analysis,latter,grammar,passage,question_num,stamp=time.time(),current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time())),file_path='static/table/Record'):
    template =f'''
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.7.2/css/all.min.css" rel="stylesheet">
    <title id='stamp'>Discussion Page {question_num}, {stamp}</title>
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
            <p style="font-size: 17px;" id="grammar">{grammar}</p>
            <p style="font-size: 14px;">语法错误数量：</p>
            <p style="font-size: 17px;" id="latter">{latter}</p>

            <script>
                            spelling = Number({latter})
                            if (spelling <=2){{
                                document.getElementById("latter").style.color = "green"
                            }} else if (spelling >2 && spelling <=5){{
                                document.getElementById("latter").style.color = "orange"
                            }} else{{
                                document.getElementById("latter").style.color = "red"
                            }}

                            // Grammar mistake coloring
                            grammar = Number({grammar})
                            if (grammar <=3){{
                                document.getElementById("grammar").style.color = "green"
                            }} else if (grammar >3 && grammar <=6){{
                                document.getElementById("grammar").style.color = "orange"
                            }} else{{
                                document.getElementById("grammar").style.color = "red"
                            {{
            </script>

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

            <h3 style="color:gray; font-size: 18px;">> Sentence-by-sentence linguistic analysis</h3>
            <p id="analysis">{analysis}</p>

            <br/><br/>

            <h3 style="color:gray; font-size: 18px;">> Your Answer</h3>
            <p id="org">{passage}</p>
            </div>
    </div>
    </body>
    </html>
'''
    filepath=file_path +f'/Discussion Page {question_num}, {stamp}.html'
    with open(filepath,'w',encoding='utf-8') as file:
        file.write(template)


    return filepath
    

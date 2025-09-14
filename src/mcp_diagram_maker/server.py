import os
import asyncio
import json
from collections.abc import Sequence
from typing import Literal, Optional, Any

import plotly.graph_objects as go
import matplotlib.pyplot as plt
from plantweb.render import render
import vl_convert as vlc
import pandas as pd
import numpy as np

from mcp.server import Server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource
)

class DiagramMakerServer(Server):
    def __init__(self):
        super().__init__(name="mcp-diagram-maker")

    def create_plotly_graph(self, python_code: Optional[str] = None, input_filepath: Optional[str] = None, output_format: Literal["png", "svg", "html"] = "png", output_path: str = "output.png") -> str:
        try:
            if input_filepath:
                with open(input_filepath, "r", encoding="utf-8") as f:
                    python_code = f.read()
            
            if not python_code:
                return "error: Pythonコードまたは入力ファイルパスのいずれかを指定する必要があります。"

            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)

            # Pythonコードを実行してfigオブジェクトを取得
            exec_globals = {'pd': pd, 'np': np, 'plt': plt, 'go': go, 'os': os} # グローバル変数に追加
            exec(python_code, exec_globals, exec_globals)
            fig = exec_globals.get('fig')

            if not isinstance(fig, go.Figure):
                return "error: Pythonコードはplotly.graph_objects.Figureオブジェクトを'fig'変数に割り当てる必要があります。"

            if output_format == "png":
                fig.write_image(output_path, format="png")
            elif output_format == "svg":
                fig.write_image(output_path, format="svg")
            elif output_format == "html":
                fig.write_html(output_path)
            else:
                return f"error: サポートされていない出力形式: {output_format}"

            return output_path
        except Exception as e:
            return f"error: Plotlyグラフの作成中にエラーが発生しました: {e}"

    def create_plantuml_diagram(self, source: Optional[str] = None, input_filepath: Optional[str] = None, output_format: Literal["png", "svg"] = "png", output_path: str = "output.png") -> str:
        try:
            if input_filepath:
                with open(input_filepath, "r", encoding="utf-8") as f:
                    source = f.read()
            
            if not source:
                return "error: PlantUMLソースまたは入力ファイルパスのいずれかを指定する必要があります。"

            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)

            # plantweb.renderを使用してPlantUML図を生成
            output_tuple = render(
                source,
                engine='plantuml',
                format=output_format,
                cacheopts={
                    'use_cache': False # キャッシュは使用しない
                }
            )
            
            # render関数は (output_bytes, format_str, engine_str, sha_str) のタプルを返す
            image_data = output_tuple[0]

            # バイナリデータとしてファイルに書き込む
            with open(output_path, "wb") as f:
                f.write(image_data)
            return output_path
        except Exception as e:
            return f"error: PlantUML図の作成中にエラーが発生しました: {e}"

    async def create_mermaid_chart(self, source: Optional[str] = None, input_filepath: Optional[str] = None, output_format: Literal["png", "svg"] = "png", output_path: str = "output.html") -> str:
        try:
            if input_filepath:
                with open(input_filepath, "r", encoding="utf-8") as f:
                    source = f.read()
            
            if not source:
                return "error: Mermaidソースまたは入力ファイルパスのいずれかを指定する必要があります。"

            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)

            if output_format == "html":
                mermaid_html = f"""
<html>
<head>
    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
    <script>
        mermaid.initialize({{ startOnLoad: true }});
    </script>
</head>
<body>
    <div class="mermaid">
    {source}
    </div>
</body>
</html>
"""
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(mermaid_html)
            elif output_format == "png":
                return "NotImplementedError: MermaidのPNG出力は未実装です。"
            elif output_format == "svg":
                return "NotImplementedError: MermaidのSVG出力は未実装です。"
            else:
                return f"error: サポートされていない出力形式: {output_format}"
            return output_path
        except Exception as e:
            return f"error: Mermaidチャートの作成中にエラーが発生しました: {e}"

    def create_vega_lite_chart(self, vl_spec: Optional[str] = None, input_filepath: Optional[str] = None, output_format: Literal["png", "svg"] = "png", output_path: str = "output.png") -> str:
        try:
            if input_filepath:
                with open(input_filepath, "r", encoding="utf-8") as f:
                    vl_spec = f.read()
            
            if not vl_spec:
                return "error: Vega-Lite仕様または入力ファイルパスのいずれかを指定する必要があります。"

            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)

            if output_format == "png":
                png_data = vlc.vegalite_to_png(json.loads(vl_spec))
                with open(output_path, "wb") as f:
                    f.write(png_data)
            elif output_format == "svg":
                svg_data = vlc.vegalite_to_svg(json.loads(vl_spec))
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(svg_data)
            else:
                return f"error: サポートされていない出力形式: {output_format}"
            return output_path
        except Exception as e:
            return f"error: Vega-Liteチャートの作成中にエラーが発生しました: {e}"

app = DiagramMakerServer()

@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="create_plotly_graph",
            description="Plotlyを使ってグラフを作成し、指定された形式で出力します。Pythonコードまたは中間ファイルパスを受け取ります。ファイルの受け渡しは絶対パスを使用する。",
            inputSchema={
                "type": "object",
                "properties": {
                    "python_code": {"type": "string", "description": "Plotlyグラフを生成するPythonコード。figオブジェクトを返す必要があります。"},
                    "input_filepath": {"type": "string", "description": "Plotlyグラフを生成するPythonコードが書かれた中間ファイルのパス。figオブジェクトを返す必要があります。"},
                    "output_format": {"type": "string", "enum": ["png", "svg", "html"], "description": "出力形式（png, svg, html）"},
                    "output_path": {"type": "string", "description": "出力ファイルの絶対パス"}
                },
                "required": ["output_format", "output_path"],
                "oneOf": [
                    {"required": ["python_code"]},
                    {"required": ["input_filepath"]}
                ]
            }
            # outputSchemaを削除
        ),
        Tool(
            name="create_plantuml_diagram",
            description="PlantUMLを使ってフロー図などを作成し、指定された形式で出力します。PlantUMLソースまたは中間ファイルパスを受け取ります。ファイルの受け渡しは絶対パスを使用する。",
            inputSchema={
                "type": "object",
                "properties": {
                    "source": {"type": "string", "description": "PlantUMLのソースコード"},
                    "input_filepath": {"type": "string", "description": "PlantUMLのソースコードが書かれた中間ファイルのパス。"},
                    "output_format": {"type": "string", "enum": ["png", "svg"], "description": "出力形式（png, svg）"},
                    "output_path": {"type": "string", "description": "出力ファイルの絶対パス"}
                },
                "required": ["output_format", "output_path"],
                "oneOf": [
                    {"required": ["source"]},
                    {"required": ["input_filepath"]}
                ]
            }
            # outputSchemaを削除
        ),
        Tool(
            name="create_mermaid_chart",
            description="Mermaidを使ってチャートを作成し、HTML形式で出力します。Mermaidソースまたは中間ファイルパスを受け取ります。ファイルの受け渡しは絶対パスを使用する。",
            inputSchema={
                "type": "object",
                "properties": {
                    "source": {"type": "string", "description": "Mermaidのソースコード"},
                    "input_filepath": {"type": "string", "description": "Mermaidのソースコードが書かれた中間ファイルのパス。"},
                    "output_format": {"type": "string", "enum": ["html"], "description": "出力形式（html）"},
                    "output_path": {"type": "string", "description": "出力ファイルの絶対パス"}
                },
                "required": ["output_format", "output_path"],
                "oneOf": [
                    {"required": ["source"]},
                    {"required": ["input_filepath"]}
                ]
            }
            # outputSchemaを削除
        ),
        Tool(
            name="create_vega_lite_chart",
            description="Vega-Liteを使ってチャートを作成し、指定された形式で出力します。Vega-Lite JSON仕様または中間ファイルパスを受け取ります。ファイルの受け渡しは絶対パスを使用する。",
            inputSchema={
                "type": "object",
                "properties": {
                    "vl_spec": {"type": "string", "description": "Vega-LiteのJSON仕様を文字列化したもの"},
                    "input_filepath": {"type": "string", "description": "Vega-LiteのJSON仕様が書かれた中間ファイルのパス。"},
                    "output_format": {"type": "string", "enum": ["png", "svg"], "description": "出力形式（png, svg）"},
                    "output_path": {"type": "string", "description": "出力ファイルの絶対パス"}
                },
                "required": ["output_format", "output_path"],
                "oneOf": [
                    {"required": ["vl_spec"]},
                    {"required": ["input_filepath"]}
                ]
            }
            # outputSchemaを削除
        ),
    ]

@app.call_tool()
async def call_tool(name: str, arguments: Any) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
    if name == "create_plotly_graph":
        result = app.create_plotly_graph(
            python_code=arguments.get("python_code"),
            input_filepath=arguments.get("input_filepath"),
            output_format=arguments["output_format"],
            output_path=arguments["output_path"]
        )
    elif name == "create_plantuml_diagram":
        result = app.create_plantuml_diagram(
            source=arguments.get("source"),
            input_filepath=arguments.get("input_filepath"),
            output_format=arguments["output_format"],
            output_path=arguments["output_path"]
        )
    elif name == "create_mermaid_chart":
        result = await app.create_mermaid_chart(
            source=arguments.get("source"),
            input_filepath=arguments.get("input_filepath"),
            output_format=arguments["output_format"],
            output_path=arguments["output_path"]
        )
    elif name == "create_vega_lite_chart":
        result = app.create_vega_lite_chart(
            vl_spec=arguments.get("vl_spec"),
            input_filepath=arguments.get("input_filepath"),
            output_format=arguments["output_format"],
            output_path=arguments["output_path"]
        )
    else:
        result = f"error: Unknown tool: {name}"

    return [
        TextContent(
            type="text",
            text=str(result)
        )
    ]

async def main():
    # イベントループの問題を回避するためにここにインポート
    from mcp.server.stdio import stdio_server

    # サーバの実行
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )

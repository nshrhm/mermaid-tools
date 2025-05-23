#!/usr/bin/env python3
import argparse
import re
import os
import subprocess
import sys
from pathlib import Path

def check_mmdc_command():
    """
    mmdc コマンドが利用可能かチェックします。
    """
    try:
        subprocess.run(["mmdc", "--version"], capture_output=True)
        return True
    except FileNotFoundError:
        print("エラー: mmdc コマンドが見つかりません。")
        print("@mermaid-js/mermaid-cli をインストールしてください:")
        print("npm install -g @mermaid-js/mermaid-cli")
        return False

def validate_mermaid_content(content):
    """
    Mermaidダイアグラムの構文を検証し、必要に応じて修正します。
    
    Args:
        content (str): 検証するMermaidダイアグラムの内容
        
    Returns:
        tuple: (is_valid, message, fixed_content) - 検証結果、メッセージ、修正されたコンテンツ
    """
    fixed_content = content
    needs_fix = False
    messages = []

    # クラス図の特別な処理
    if content.strip().startswith('classDiagram'):
        lines = content.split('\n')
        fixed_lines = []
        
        for i, line in enumerate(lines, 1):
            fixed_line = line
            if 'class' in line and '"' in line:
                # クラス定義行のクォートを削除
                needs_fix = True
                fixed_line = re.sub(r'class\s*"([^"]+)"', r'class \1', fixed_line)
                fixed_line = re.sub(r'"([^"]+)"\s*{', r'\1 {', fixed_line)
                messages.append(f"警告: 行 {i}: クラス名からクォートを削除しました")
            elif '<|--' in line and '"' in line:
                # 継承関係のクォートを削除
                needs_fix = True
                fixed_line = re.sub(r'"([^"]+)"', r'\1', fixed_line)
                messages.append(f"警告: 行 {i}: 継承関係のクラス名からクォートを削除しました")
            elif '-->' in line and '"' in line:
                # 関連のクォートを削除
                needs_fix = True
                fixed_line = re.sub(r'"([^"]+)"', r'\1', fixed_line)
                messages.append(f"警告: 行 {i}: 関連のクラス名からクォートを削除しました")
            fixed_lines.append(fixed_line)
        
        if needs_fix:
            fixed_content = '\n'.join(fixed_lines)
            return False, '\n'.join(messages), fixed_content
    
    return True, "OK", fixed_content

def convert_to_image(mmd_file, formats=None, output_base=None):
    """
    MermaidファイルをSVGやPNGに変換します。
    
    Args:
        mmd_file (str): 入力.mmdファイルのパス
        formats (list): 出力形式のリスト（デフォルト: ["svg"]）
        output_base (str): 出力ベースディレクトリ（デフォルト: カレントディレクトリ）
    """
    if formats is None:
        formats = ["svg"]
    if output_base is None:
        output_base = "."
    
    input_path = Path(mmd_file)
    base_name = input_path.stem
    success = True
    
    for fmt in formats:
        if fmt == "mmd":
            continue
            
        # 出力ディレクトリの作成
        output_dir = os.path.join(output_base, fmt)
        os.makedirs(output_dir, exist_ok=True)
        
        # 出力ファイルパスの構築
        output_file = os.path.join(output_dir, f"{base_name}.{fmt}")
        
        print(f"{mmd_file} -> {output_file} を変換中...")
        try:
            result = subprocess.run(
                ["mmdc", "-i", mmd_file, "-o", output_file],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                print(f"警告: {output_file} の生成中にエラーが発生しました。")
                print(f"エラー出力: {result.stderr}")
                success = False
            else:
                print(f"{output_file} を生成しました。")
        except Exception as e:
            print(f"エラー: {output_file} の生成中に問題が発生しました - {e}")
            success = False
    
    return success

def is_mermaid_content(content):
    """
    テキストがMermaid記法かどうかを判定します。
    """
    content = content.strip()
    mermaid_starts = ('graph ', 'sequenceDiagram', 'classDiagram', 'stateDiagram',
                     'erDiagram', 'pie', 'gantt', 'flowchart ', 'journey')
    return content.startswith(mermaid_starts)

def extract_and_save_mermaid_diagrams(input_filepath, formats=None, output_dir=".", validate_only=False):
    """
    ファイルからMermaidダイアグラムを抽出し、個別のファイルとして保存します。
    ```mermaid ... ```ブロックまたは直接のMermaid記法に対応します。
    """
    try:
        with open(input_filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"エラー: ファイルが見つかりません - {input_filepath}")
        return
    except Exception as e:
        print(f"エラー: ファイルの読み込み中に問題が発生しました - {e}")
        return

    # 入力ファイルのパスを解析
    input_path = Path(input_filepath)
    if input_path.parent.name == "mmd":
        print("警告: mmdディレクトリ内のファイルは処理しません")
        return

    # Markdownブロックとしての抽出を試行
    # コードブロックを正確に検出
    # 1. バッククォート3つで始まる
    # 2. "mermaid" キーワード（前後の空白を許可）
    # 3. 改行を含む任意のコンテンツ
    # 4. バッククォート3つで終わる
    mermaid_pattern = re.compile(r'```[^\S\n]*mermaid[^\S\n]*\n(.*?)\n[^\S\n]*```', re.DOTALL)
    matches = mermaid_pattern.findall(content)

    # Markdownブロックが見つからない場合、直接のMermaid記法として処理
    if not matches and is_mermaid_content(content):
        matches = [content]

    if not matches:
        print(f"情報: ファイル '{input_filepath}' からMermaidダイアグラムは見つかりませんでした。")
        return

    # 出力用のベースディレクトリを作成
    output_base = os.path.join(output_dir, "output")
    mmd_dir = os.path.join(output_base, "mmd")
    os.makedirs(mmd_dir, exist_ok=True)

    # ベースファイル名を取得（拡張子を除く）
    base_filename = input_path.stem

    output_count = 0
    for i, diagram_content in enumerate(matches):
        # 構文の検証と修正
        is_valid, message, fixed_content = validate_mermaid_content(diagram_content)
        if not is_valid:
            print(f"警告: 図 {i+1} の構文に問題があります:")
            print(message)
            if validate_only:
                continue
            print("自動修正を適用します。")
        elif validate_only:
            print(f"図 {i+1} の構文は正常です。")

        # .mmdファイルとして保存
        # 複数のダイアグラムがある場合は連番を付加
        if len(matches) > 1:
            output_filename = os.path.join(mmd_dir, f"{base_filename}_{i+1:02d}.mmd")
        else:
            output_filename = os.path.join(mmd_dir, f"{base_filename}.mmd")

        try:
            with open(output_filename, 'w', encoding='utf-8') as f:
                f.write(fixed_content.strip())
            print(f"Mermaidダイアグラムを '{output_filename}' に保存しました。")
            output_count += 1

            # 画像形式への変換
            if not validate_only and formats and any(fmt != "mmd" for fmt in formats):
                convert_to_image(output_filename, formats, output_base=output_base)

        except Exception as e:
            print(f"エラー: '{output_filename}' への書き込み中に問題が発生しました - {e}")
            
    print(f"合計 {output_count} 個のMermaidダイアグラムを処理しました。")

def main():
    parser = argparse.ArgumentParser(
        description="ファイルからMermaidダイアグラムを抽出し、個別のファイルとして保存します。"
    )
    parser.add_argument(
        "input_file",
        help="Mermaidダイアグラムを含む入力ファイルのパス"
    )
    parser.add_argument(
        "--formats",
        nargs="+",
        choices=["mmd", "svg", "png"],
        default=["mmd"],
        help="出力形式を指定します（デフォルト: mmd）"
    )
    parser.add_argument(
        "--output-dir",
        default=".",
        help="出力ディレクトリを指定します（デフォルト: カレントディレクトリ）"
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="構文の検証のみを行い、ファイルは生成しません"
    )
    
    args = parser.parse_args()

    # 画像形式が指定されている場合はmmdc コマンドの確認
    if any(fmt != "mmd" for fmt in args.formats) and not check_mmdc_command():
        sys.exit(1)
    
    extract_and_save_mermaid_diagrams(
        args.input_file,
        formats=args.formats,
        output_dir=args.output_dir,
        validate_only=args.validate_only
    )

if __name__ == "__main__":
    main()

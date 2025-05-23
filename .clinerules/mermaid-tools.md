## Brief overview
このプロジェクト固有のガイドラインで、Mermaidダイアグラム抽出ツールの開発に関する規則を定義します。

## Communication style
- 日本語での応答を優先
- コマンド実行時は目的と期待される結果を明確に説明
- エラーメッセージは日本語で分かりやすく表示

## Development workflow
- 標準ライブラリの使用を優先し、外部依存は最小限に
- コマンドライン引数は`argparse`で処理
- 出力ディレクトリ構造は`output/{mmd,svg,png}/`形式に統一

## Coding best practices
- 関数は明確な単一の責任を持つように設計
- エラーハンドリングは詳細なメッセージを提供
- 正規表現パターンは非貪欲マッチングを使用

## Documentation standards
- READMEは日本語版（README_ja.md）と英語版（README.md）を提供
- 各スクリプトのヘルプメッセージは詳細な使用例を含める
- コマンドラインオプションは一貫した命名規則に従う

## Project preferences
- Python 3.x での開発
- 出力ファイル名は連番形式（`sample_01.mmd`など）
- メモリーバンクによるプロジェクト文書管理

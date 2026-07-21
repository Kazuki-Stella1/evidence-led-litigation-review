# 完全架空の校正デモ

このディレクトリは、誤変換、重複入力、括弧不整合、未登録号証及び主張・号証対応のずれを、行・文字位置付きで一覧化するための完全架空fixtureです。

```bash
python scripts/run_proofreading_demo.py
```

成果物は `output/proofreading/` のMarkdown、JSON及びUTF-8 BOM付きCSVです。行番号は抽出テキスト基準であり、Word又はPDFの表示行とは限りません。

# Changelog
変更内容はこのファイルに記載します。

このフォーマットは [Keep a Changelog](https://keepachangelog.com/ja/1.0.0/) に基づいています。
バージョン番号は [Semantic Versioning](https://semver.org/lang/ja/spec/v2.0.0.html) を参考にしています。

## [Unreleased]

## [1.1.1] - 2020-07-04
### Fixed
- UVの切れ目の判定を修正
  - 差がわずかな場合は繋がっているものと扱う
- CHANGELOG.md の記法のミスの修正

## [1.1.0] - 2020-06-06
### Added
- 材質モーフをXMLに保存
- ボーンモーフをXMLに保存
- グループモーフをXMLに保存
- 材質のメモをXMLに保存
- エクスポート終了時にメッセージを表示

### Changed
- インポート・エクスポート時に検証する項目を追加
- XMLの改行を調整
- XMLに書き出す小数点の精度を変更

### Fixed
- ビューポートで無効なオブジェクトのエクスポート時のエラーを修正
- 非表示コレクションがある場合のエクスポート時のエラーを修正
- エクスポート結果に不正法線が出力されていたのを修正
- Blender 2.83でTスタンス・Aスタンス変更がおかしくなっていたのを修正

## [1.0.5] - 2020-03-03
### Fixed
- 空のマテリアルスロットが存在する場合にエラーが発生していたのを修正

## [1.0.4] - 2020-02-18
### Fixed
- PMX上の材質のテクスチャに指定された画像ファイルが無い場合に、インポートで意図しないエラーが発生していたのを修正
- 2.82で日本語ボーン名のアーマチュア雛形をアペンドしたときに、環境によってエラーが発生していたのを修正

## [1.0.3] - 2020-01-21
### Fixed
- 一部のボーンの並び替えの判定の間違いを修正

## [1.0.2] - 2019-12-12
### Fixed
- 2.81でインポート時に発生していたエラーを修正

## [1.0.1] - 2019-11-24
### Fixed
- 非表示オブジェクトに対するモディファイアー適用処理時のエラーを修正

## [1.0.0] - 2019-10-27
### Changed
- ボーンの並び順をXMLの並び順にするように変更
- XMLのconstraint要素のbody_A属性とbody_B属性を剛体名に変更
- サンプルファイルをblender2pmxem仕様に変更

### Added
- 簡易な検証処理を追加

## [0.1.2] - 2019-10-12
### Fixed
- プリンシパルBSDFノードが無いマテリアルのエクスポート時のエラーを修正

## [0.1.1] - 2019-09-28
### Fixed
- 「ドライバーを追加」実行時のエラーを修正

## [0.1.0] - 2019-09-22
### Changed
- Blender 2.80のアドオンAPIへの対応
- それに伴う仕様変更
  - インポーター・エクスポーターの、材質・マテリアルの扱い方
  - UIをサイドバーに移動

### Removed
- 移行が難しかった機能の削除
  - 輪郭線機能
  - Mat to tex
  - 陰影なしチェックボックス

[Unreleased]: https://github.com/matunnkazumi/blender2pmxem/compare/1.1.1...HEAD
[1.1.1]: https://github.com/matunnkazumi/blender2pmxem/compare/1.1.0...1.1.1
[1.1.0]: https://github.com/matunnkazumi/blender2pmxem/compare/1.0.5...1.1.0
[1.0.5]: https://github.com/matunnkazumi/blender2pmxem/compare/1.0.4...1.0.5
[1.0.4]: https://github.com/matunnkazumi/blender2pmxem/compare/1.0.3...1.0.4
[1.0.3]: https://github.com/matunnkazumi/blender2pmxem/compare/1.0.2...1.0.3
[1.0.2]: https://github.com/matunnkazumi/blender2pmxem/compare/1.0.1...1.0.2
[1.0.1]: https://github.com/matunnkazumi/blender2pmxem/compare/1.0.0...1.0.1
[1.0.0]: https://github.com/matunnkazumi/blender2pmxem/compare/0.1.2...1.0.0
[0.1.2]: https://github.com/matunnkazumi/blender2pmxem/compare/0.1.1...0.1.2
[0.1.1]: https://github.com/matunnkazumi/blender2pmxem/compare/0.1.0...0.1.1
[0.1.0]: https://github.com/matunnkazumi/blender2pmxem/releases/tag/0.1.0

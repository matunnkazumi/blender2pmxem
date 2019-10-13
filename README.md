# blender2pmxem

blender2pmxeをBlender2.80系に対応させたい(願望)

## 概要

PMX形式のファイルのインポート・エクスポートを行うBlenderアドオンです。

KAGAYAS氏の改変Blender2Pmxe([配布ミラー](https://bowlroll.net/file/145391))を、Blenderの2.80向けに改変したものです。

## ライセンス
改変元のライセンスに従います。

それ以外の完全に新規に作成したファイルは [CC0](https://creativecommons.org/publicdomain/zero/1.0/legalcode) です。

## 進捗
とりあえず動いているっぽい。

## Blender2Pmxe からの仕様の変更点

* インポート・エクスポート
  * PMX形式の材質の設定は、BlenderのマテリアルのプリンシプルBSDFノードと対応させています
    * 拡散色 → ベースカラー
    * テクスチャファイル → ベースカラーの画像テクスチャノードのファイル
  * 材質色、スフィアマップ設定は、モデル情報のXMLに保存・取得するようにしました
* ツールのUI
  * ツールシェルフからサイドバーに移動しました
  * 以下を削除しました
    * 輪郭線機能
    * Mat to tex
    * 「陰影なし」チェックボックス
* XML
  * ボーンの並び順をXMLの順番でエクスポートするようにしました
  * constraints要素のbody_Aとbody_Bを剛体名に変更しました

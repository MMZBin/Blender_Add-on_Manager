# Blender Add-on Manager

__注意: このプロジェクトで使用されている英語は日本語から機械翻訳されたものがベースになっているため、不自然な表現がある可能性があります。__

[Click here for the README in English.](/README.md)

## 概要
Blender Add-on ManagerはBlender Python APIを使ったBlenderアドオン開発を支援するフレームワークです。

アドオンに関連するクラスの登録や解除、キーマップやカスタムプロパティの管理などを抽象化します。

## 使い方
プロジェクトフォルダにこのリポジトリを配置し、同じ階層の`modules`フォルダにモジュールを作成することで機能します。

## 機能
- アドオンに関連するクラス(`Operator`, `Panel`, `PropertyGroup`やその他)の登録、解除の自動化
- キーマップの登録、解除の抽象化
- カスタムプロパティの登録、取得、解除の抽象化
- 一部の定数を提供


### アドオンクラス管理機能([AddonManager](/addon_manager.py))
- `modules`フォルダ内に存在するモジュールとその中で定義されているアドオンに関連するクラス(`bpy.types.bpy_struct`を継承しているクラス)を自動で取得し、Blenderに登録/解除します。
- ファイルシステムをスキャンした場合(`is_debug_mode = true`か`module.pkl`が存在しない場合)、起動時にコンソールにログが表示されます。
    - 読み込みが完了すると[data](/data/)フォルダ以下に`modules.pkl`が作成され、`is_debug_mode = false`の場合はこのキャッシュからモジュールを読み込みます。
- 各モジュール内に`register()`関数や`unregister()`関数が存在する場合、アドオンの登録時と解除時に呼び出されます。
    - もしこれらの関数が引数を取る場合、対応する[AddonManager](/addon_manager.py)インスタンスが渡されます。
    - モジュールが`disabled`に指定されている場合は呼び出されません。
        - [config.toml](/data/config.toml)
            - 読み込みに関する設定を保存します。
                - `is_debug_mode`(boolean)
                    - デバッグモードを有効にするかを指定します。
                        - `true`の場合は必ずファイルシステムをスキャンします。
                        - `false`の場合は`modules.pkl`ファイルが存在しない場合のみファイルシステムをスキャンし、存在する場合はキャッシュから読み込みます。
                - `disabled`(list of string)(任意)
                    - 無効にするモジュールを指定します。
                    - 指定したモジュールとそのサブモジュールが無視されます。
                    - 例:
                        ```toml
                        disabled = [
                            "spam.ham" # /modules/spam/ham 以下のモジュールが無視されます。
                        ]
                        ```
                - `priorities`(list of string)(任意)
                    - モジュールの読み込み順を指定します。
                    - 例
                        ```toml
                        # spam -> eggsの順番でBlenderに登録されます。
                        priorities = [
                            "spam",
                            "eggs"
                        ]
                        ```
        - [decorators](/core/loader/decorators.py)
            - モジュール内のアドオンクラスに関する情報を設定します。
                - `@disable`デコレータ
                    - このデコレータを付けたクラスは読み込み時に無視されます。
                - `@priority`デコレータ
                    - このデコレータに渡した番号が小さいほど先に読み込まれます。
                    - 同じモジュール内でのみ比較されます。

### キーマップ管理機能([KeymapManager](/features/keymap_manager.py))
- キーマップの管理を抽象化します。
- シングルトンクラスです。
- `add()`メソッドでキーマップを登録し、`delete()`メソッドで削除します。
- アドオン自体がBlenderから解除される際は自動でキーマップも削除されます。
- 例:
```python
def register() -> None:
    KeymapManager().add(Key(Your_Operator, "F1", "PRESS"))
```

### カスタムプロパティ管理機能([PropertiesManager](/features/properties_manager.py))
- カスタムプロパティの管理を抽象化します。
- シングルトンクラスです。
- 名前の衝突を避けるため、`[アドオンフォルダ名]_`をプロパティ名に追加します。
- `add()`メソッドでプロパティを登録し、`delete()`メソッドで削除します。
- `get()`メソッドでプロパティを取得します。プロパティそのものではなく[Property](/features/properties_manager.py)オブジェクトであることに __注意__ してください。
- アドオン自体がBlenderから解除される際は自動でプロパティも削除されます。
- 例:
```python
# 登録
def register() -> None:
    PropertiesManager().add(bpy.types.Scene, ("your_prop_name", Your_PropertyGroup))
#使用
prop  = PropertiesManager().get(bpy.context.scene, "your_prop_name")
value = prop.get("your_prop_attribute") # プロパティを取得する
prop.set("your_prop_attribute", True)   # プロパティを設定する
```

### 定数([constants](/constants.py))
- オペレーターの`execute()`メソッドの戻り値やオブジェクトの種類などが定数として定義されています。

## サンプル
フォルダ構造の例:
```
your_addon/
├── manager/
│   ├── core
│   │   └── ...省略...
│   ├── features
│   │   └── ...省略...
│   └── ...省略...
├── modules/
│   └── ここにモジュールを配置
├── __init__.py
└── blender_manifest.toml
```
`__init__.py`ファイルの例:
```python
from .manager.addon_manager import AddonManager

addon = AddonManager()

# AddonManager.register()メソッドとunregister()メソッドはアドオンの登録時と解除時に呼び出される必要があります。

def register() -> None:
    addon.register()


def unregister() -> None:
    addon.unregister()
```

モジュール(パネル)の例:

`/modules/sample_panel.py`
```python
from bpy.types import Panel, Context

class SamplePanel(Panel):
    bl_label = "Sample operator"
    bl_idname = "VIEW3D_PT_sample_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'sample'

    def draw(self, context: Context) -> None:
        layout = self.layout

        layout.label(text="This is sample panel.")

# これらの関数は必須ではありません。

def register() -> None:
    print("sample_panel.py is now registered.")

def unregister() -> None:
    print("sample_panel.py is now unregistered.")
```


## 注意点
- モジュールをインポートする際、エディタの自動補完(`from manager. ...`の形)では実行時にエラーが発生する可能性があります。
    - もしエラーになった場合は相対パスによるインポート(`from ...manager import ...`のような形)に変更してみてください。

## ライセンス
このプログラムはMITライセンス下で公開されています。
詳細は[LICENSE](/LICENSE)ファイルを確認してください。

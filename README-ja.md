# Blender Add-on Manager

__注意: このプロジェクトで使用されている英語は日本語から機械翻訳されたものがベースになっているため、不自然な表現がある可能性があります。__

[Click here for the README in English.](/README.md)

## 概要
Blender Add-on ManagerはBlender Python APIを使ったBlenderアドオン開発を支援するフレームワークです。

アドオンに関連するクラスの登録や解除、キーマップやプロパティの管理などを抽象化します。

## 使い方
プロジェクトフォルダにこのリポジトリを配置し、同じ階層の`modules`フォルダにモジュールを作成することで機能します。

## 機能
- アドオンに関連するクラス(`Operator`, `Panel`, `PropertyGroup`やその他)の登録、解除の自動化
- キーマップの登録、解除の抽象化
- プロパティグループの登録、取得、解除の抽象化と型定義の提供
- 一部の定数を提供


### アドオンクラス管理機能([AddonManager](/addon_manager.py))
- `modules`フォルダ内に存在するモジュールとその中で定義されているアドオンに関連するクラス(`bpy.types.bpy_struct`を継承しているクラス)を自動で取得し、Blenderに登録/解除します。
    - ただし、`bpy.types.WorkSpaceTool`のサブクラスは除外しているので手動で登録してください。
- マネージャーのフォルダ直下に`data`フォルダを作成し、設定やキャッシュを格納します。
- ファイルシステムをスキャンした場合(`is_debug_mode = true`か`module.pkl`が存在しない場合)、起動時にコンソールにログが表示されます。
    - 読み込みが完了すると`data`フォルダ以下に`modules.pkl`が作成され、`is_debug_mode = false`の場合はこのキャッシュからモジュールを読み込みます。
    -  __特別な理由がない限り、アドオンをリリースする際は`is_debug_mode = false`に設定したうえで`modules.pkl`を含めないようにするほうが良いでしょう。__
- 各モジュール内に`register()`関数や`unregister()`関数が存在する場合、アドオンの登録時と解除時に呼び出されます。
    - もしこれらの関数が引数を取る場合、対応する[AddonManager](/addon_manager.py)インスタンスが渡されます。
    - モジュールが`disabled`に指定されている場合は呼び出されません。
- `config.toml`
    - 読み込みに関する設定を保存します。
    - 存在しない場合、起動時に生成されます。
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
        - `exclude_patterns`(list of string)(任意)
            - この項目に指定した文字列は無視されます。
            - 例
            ```toml
                exclude_patterns = [
                    "__" # パスに"__"を含むモジュールが無視されます。
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
- 静的クラスです。
- `add()`メソッドでキーマップを登録し、`delete()`メソッドで削除します。
- アドオン自体がBlenderから解除される際は自動でキーマップも削除されます。
- 例:
```python
def register() -> None:
    KeymapManager.add(KeyInfo(Your_Operator, "F1", "PRESS"))
```

### プロパティグループ管理機能([PropertyGroupManager](/features/property_group_manager.py))
- プロパティグループの管理を抽象化します。
- 静的クラスです。
- 型とキーを元にプロパティを登録し、`[アドオンフォルダ名]_[プロパティクラス]_[プロパティグループのクラスか型定義のクラスのID]_[キー]`の形でBlenderにアタッチします。
- `add()`メソッドでプロパティを登録し、`delete()`メソッドで削除します。
- `get()`メソッドでプロパティを取得します。
- アドオン自体がBlenderから解除される際は自動でプロパティも削除されます。
- 設定することで各プロパティに対する型定義を利用することができますが、プロパティ本体と型定義のフィールド名や型に食い違いがあると型ヒントが正しく動作しません。
    - 実際には、警告を無視してプロパティ型のオブジェクトを型定義用の型に割り当てているだけです。
- 例:
```python
# プロパティグループの定義の例

# プロパティ本体
class Your_PropertyGroup(bpy.types.PropertyGroup):
    bool_prop: bpy.props.BoolProperty(name="Your bool prop")
    int_prop:  bpy.props.IntProperty(name="Your int prop")

# 型定義(プロパティ本体名の後ろに"Type"を付けてください。)(任意)
# このクラスは型データの付与にのみ使用され、実際のデータには影響を与えません。
class Your_PropertyGroupType:
    bool_prop: bool
    int_prop: int

# 登録
def register() -> None:
    PropertyGroupManager.add(bpy.types.Scene, PropertyInfo(Your_PropertyGroup, Your_PropertyGroupType))
    # PropertyGroupManager.add(bpy.types.Scene, PropertyInfo(Your_PropertyGroup, Your_PropertyGroupType, "custom_key")) # keyを指定することで同じ型の複数のプロパティを登録できます。

#使用
prop  = PropertyGroupManager.get(bpy.context.scene, Your_PropertyGroupType) # 指定した型とキーのプロパティを取得します。(型定義を使用した場合はそのクラスを使ってアクセスしないと動作しません。)
# prop  = PropertyGroupManager.get(bpy.context.scene, Your_PropertyGroupType, "custom_key")
# prop  = PropertyGroupManager.get(bpy.context.scene, Your_PropertyGroup) # 型定義を利用しない場合はプロパティ本体の型を指定してください。

value = prop.bool_prop # プロパティの取得
prop.int_prop = 100    # プロパティの設定
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
│   └── [ここにモジュールを配置]
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

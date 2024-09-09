This library uses English that has been machine-translated from Japanese.

__[The English readme is here](README.md)__

# __このスクリプトは開発中のため、破壊的な変更が加えられる可能性があります。__

# Blender_Add-on_Manager
Blenderアドオンを構成するファイルの動的な登録・解除を実現するスクリプトです。
クラスの登録・解除・無効化・優先順位付け・ショートカットキーの登録といった面倒な作業を自動で行うことができます。
Blender 4.1で動作確認しています。

読み込み対象の基底クラスは[`/core/proc_loader.py`](/core/proc_loader.py)の`ProcLoader`クラス内にある`TARGET_CLASSES`クラス変数に書いてあります。

基本的なクラスは網羅しているつもりですが、抜けているクラスや余計なクラスがあったらお知らせください。

任意のクラスを指定することも可能です。

## クイックスタート
1. アドオンフォルダ内にこのスクリプトを配置(適当な名前のフォルダに入れてください。)このREADMEでは`manager`フォルダ内に入れる想定です。
2. `__init__.py`ファイル内で`AddonManager`クラスのインスタンスを生成
3. `AddonManager`インスタンスの`register()`メソッドと`unregister()`メソッドを同じ名前のグローバル関数でラップする
4. 指定したフォルダ内に使いたいオペレーターを含むファイルを配置する

### サンプルコード

`__init__.py`
```python
from .manager.core.register_addon import AddonManager #AddonManagerクラスをインポートする

#アドオンの情報
bl_info = {
    "name": "Addon_name",
    "author": "your_name",
    "version": (1, 0, 0),
    "blender": (4, 1, 0),
    "location": "View3D > Tools > Addon_name",
    "description": "",
    "category": "General",
}

addon = AddonManager(__file__, locals(), is_debug_mode=True) #AddonManagerクラスのインスタンスを生成する
                                                             #is_debug_modeがTrueの場合のみアドオンのファイルを探索します。(Falseの場合はキャッシュファイルから読み込みます。)

#'register()'メソッドと'unregister()'メソッドをラップする
def register(): addon.register()
def unregister(): addon.unregister()
```
`operators/hoge.py`
```python
'''F1キーが押されたときに通知を表示するスクリプト'''

from bpy.types import Operator

#ショートカットキーを登録するための`Key`データクラスと`keymapManagerクラスをインポートする`
from ..manager.core.keymap_manager import Key

class HOGE_OT_Sample(Operator):
    bl_idname = "hoge.sample_operator"
    bl_label = "Test Operator"
    bl_description = "Test."

    def execute(self, context):
        self.report({'INFO'}, "HOGE_OT_Sample!!!!!!!!!!!!!!")

        return {"FINISHED"}

def register(manager):
    manager.keymap.add(Key(HOGE_OT_Sample, 'F1')) #F1キーが押されたときに'HOGE_OT_Sample'オペレーターが実行されるように設定する
```


## 機能
- サブディレクトリを含めて、アドオンフォルダ内のすべてのアドオンのクラスを登録・解除します。
    - `.`から始まるフォルダと`core`フォルダの親フォルダ、AddonManagerクラスのコンストラクタで指定したフォルダは無視されます。
- `AddonManager`クラスのコンストラクタの`is_debug_mode`が`True`の場合のみアドオンのモジュールやクラスを探索し、`False`の場合は既存のキャッシュファイルから読み込みます。
    - フォルダの構造やファイル構成が変更された場合は、一度`is_debug_mode`を`True`に設定して起動してください。(その後は`False`にしてもかまいません。)
- 各ディレクトリの`__init__.py`に`disable`という名前のリストを定義し、モジュール名を記述することでそのモジュールを無視します。
    - モジュールのパスはリストが定義されている`__init__.py`ファイルが存在するディレクトリから見た相対パスです。
        - 例(`operators`フォルダ内の`__init__.py`ファイルの場合): `ignore = ['your_operator']`
- 各ディレクトリの`__init__.py`に`priority`という名前のリストを定義し、モジュール名を記述することでモジュールがその順序で読み込まれます。
        - 例(`operators`フォルダ内の`__init__.py`ファイルの場合): `ignore = ['your_operator', 'your_operator2']`
    - 指定しなかった場合の読み込み順は保証されません。
- `disable`デコレータを使うことで特定のクラスを無視することができます。
    - 例: `@disable`
- `priority`デコレータを使うことで特定のクラスの読み込み順を制御することができます。
    - 値が`0`以上で小さいほど優先度が高くなります。
    - 例: `@priority(42)`
- `KeymapManager`クラスを使用することでショートカットキーを登録することができます。
    - キーマップの削除は自動で行われます。
    - 例: `manager.keymap.add(Key(HOGE_OT_YourOperator, 'A'))`
- `PropertiesManager`クラスを使用することでプロパティグループを登録・参照・解除することができます。(初期の構成では`AddonManager`クラスの`addon_name`引数が必要になります。)
    - プロパティの削除は自動で行われます。
    - 例
        - プロパティの登録: `manager.property.add(Scene, [("your_properties", YourPropertyGroupClass)])`
        - プロパティの参照:
        ```python
            prop = manager.property.get(bpy.context.scene, "your_properties") #プロパティの取得
            value = prop.get('your_attribute') #プロパティの属性の取得
            prop.set('your_attribute', 'Hello, world!') #プロパティの値を設定
        ```
- `bl_idname`を省略でき、省略した場合は自動的にクラス名が割り当てられます。(クラス名が競合する際は明示的に設定してください。)
- `bpy.types.Panel`を継承したクラスの場合、`AddonManager`のコンストラクタで任意の名前を設定することで`bl_category`属性を省略できます。(明示的に設定した場合はそれが優先されます。)
- デバッグ向けの機能もいくつか搭載されています。
    - `AddonManager`クラスの`is_debug_mode`引数によって有効化できます。
        - 無効にすると、各ディレクトリ直下に`debug`ディレクトリが存在する場合、その中にあるモジュールが無視されます。
        - 有効にすると`debug`ディレクトリ内のモジュールが読み込まれ、`script.reload`が実行された際にモジュールが再読込されるようになります。

- 読み込み対象の各モジュールにregister()関数やunregister()関数がある場合、アドオンの登録・解除の際に呼び出されます。
    - これらの関数が引数を取る場合、クラスが登録される際に対応する`AddonManager`インスタンスが渡されます。
- アドオンのクラスが`set_manager()`というクラスメソッドを持つ場合、対応する`AddonManager`インスタンスが渡されます。
    - 例：
        ```python
            class AddonClass(bpy.types.Operator):
                @classmethod
                def set_manager(manager):
                    self.__manager = manager
        ```
- Blender標準形式の翻訳辞書を使用して多言語に対応させることができます。
- `constants.py`にオペレーターの戻り値やモード名などいくつかの定数が用意されているため、入力の手間とタイプミスを減らすことができます。
- `DrawText`クラスを使ってテキストの描画を簡素化できます。(ドキュメント未作成)

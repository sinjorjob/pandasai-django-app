
# pandasai-django-app

pandas-ai を組み込んだ Django アプリケーションです。

[pandas-ai GitHub リポジトリ](https://github.com/Sinaptik-AI/pandas-ai?tab=readme-ov-file)

![pandas-ai-django-app logo](https://example.com/pandasai-django-app-logo.png)

## 動作確認環境

- Python: 3.11.5
- Django: 5.1.1

## 起動手順

1. 仮想環境の作成と有効化
   ```
   python -m venv <仮想環境名>
   <仮想環境名>\scripts\activate
   ```

2. 依存関係のインストール
   ```
   pip install -r requirements.txt
   ```

3. プロジェクトディレクトリに移動
   ```
   cd <project-folder>
   ```

4. データベースのセットアップ
   ```
   python manage.py makemigrations pandasai_app
   python manage.py migrate
   ```

5. 管理者ユーザーの作成
   ```
   python manage.py createsuperuser
   ```

6. サーバーの起動
   ```
   python manage.py runserver
   ```

7. ブラウザで `http://127.0.0.1:8000/` にアクセスして動作確認

## 初期データの登録（LLMモデル）

以下のコマンドを実行して LLM モデルの初期データを登録します：

```
python manage.py init_model_data
```

成功時のメッセージ：
```
Model data initialized successfully with gpt-4o-mini preset for all providers.
Successfully initialized AI model data
```

## LLMモデルの設定

- OpenAI と AzureOpenAI の 2 つのプロバイダーが利用可能
- デフォルトでは OpenAI が Active 状態
- 一度に 1 つのプロバイダーのみを Active に設定可能
- 初期設定：
  - モデル：gpt-4o-mini
  - API キー：「default_key_please_change」（実際の API キーに変更が必要）
- 利用可能なモデル名は「AI model names」に登録されたものがリスト表示されます
- モデル名は必要に応じて admin 画面から追加可能です

## アプリの利用方法

http://127.0.0.1:8000/ にアクセスすると以下のような画面が表示されます。

![メイン画面](https://example.com/main-screen.png)

### 1. モデルの設定

画面右上の「モデル設定」を押すと以下の画面が表示されるので、利用するプロバイダの「セットアップ」ボタンをクリックします。

![モデル設定画面](https://example.com/model-setup-screen.png)

モデル名、API キーを入力してアクティブ UI を有効にした状態で保存します。
AzureOpenAI の場合は、API Version と Endpoint も登録します。
有効にできるモデルは 1 つだけです。

### 2. 質問の投げ方

1. 画面上部の「CSV ファイル、または Excel ファイルをここにドラッグ&ドロップするか、クリックしてファイルを選択してください」の欄に csv、もしくは Excel ファイルをアップロードします。

2. アップロードすると以下の様に自動的にファイルの内容を読み取りテーブル形式で表示します。
   ※綺麗なテーブル形式のデータ以外は正しく読み取れないので注意。

   ![テーブル表示](https://example.com/table-display.png)

   - 「検索」ボックスに文字列を入れると文字列検索ができます。
   - 各列をクリックすると、「昇順、降順」にソートすることができます。

3. 「質問を入力してください：」の欄にアップロードしたファイルに対する指示文を入力します。

4. 「出力形式」から以下のいずれかを選択してください。
   - graph: グラフを表示してほしい場合
   - dataframe: 表形式の結果を返してほしい場合
   - string: 文字列（文章）の回答が欲しい場合

### サンプルデータを使用した例

サンプルデータの「プロジェクト収支データ.csv」をアップロードした状態でそれぞれ以下のような指示出しを行います。

#### graph の例

```
以下の条件で、プロジェクト毎の利益率の推移がわかる折れ線グラフを描画してください。

#条件
プロジェクト毎に違う色で利益率の折れ線グラフを描画する
値のラベルを表示する。
凡例はグラフの外側に表示する。
縦、横に Grid 線を表示する。
横幅をできるだけ長くして見やすいレイアウトにしてください。
```

![グラフ結果](https://example.com/graph-result.png)

#### dataframe の例

```
プロジェクト毎の総売上と総利益を計算し、利益率順に並べ替えて表示してください。
```

![データフレーム結果](https://example.com/dataframe-result.png)

#### string の例

```
最も利益率の高いプロジェクトと最も低いプロジェクトを比較し、その理由を分析してください。
```

![文字列結果](https://example.com/string-result.png)


# HP係 事前準備マニュアル

廣澤研究室のHPを運営する係で、まず事前準備としてやってほしいことをこのページにまとめる。

## HPの運用方式

基本的にHTMLとCSSで構成されたファイルを編集して更新します。
作業の流れは以下の通りです：

> **git pull で最新版を取得 → Cursor でHTML編集 → Codex（AIエージェント）に指示 → Live Server でブラウザ確認 → git commit/push で変更記録 → FileZilla でサーバーにアップロード → 実URLで最終確認（完了）**

---

## やってほしいことリスト

1. **Git の設定**
2. **リポジトリのクローン（HP ファイル一式の取得）**
3. **大容量フォルダの取得（ギガファイル便）**
4. **Cursor のセットアップ**
5. **Codex（AIエージェント）のセットアップ**
6. **FileZilla のインストール**
7. **運用マニュアルの熟読**

---

## 1. Git の設定

Git はファイルの変更履歴を管理するバージョン管理ツールです。変更の差分確認、バックアップ、GitHubとの連携に使います。

**公式サイト：** https://git-scm.com

### インストール

1. https://git-scm.com/downloads/win にアクセスする
2. 「Click here to download」をクリックしてインストーラー（`.exe`）をダウンロードする
3. ダウンロードした `.exe` を実行し、以下の点だけ設定を変更して「Next」を押し続ける：

| 設定画面 | 推奨設定 |
|---|---|
| Choosing the default editor | `Use Visual Studio Code as Git's default editor` を選択 |
| Initial branch name | `Override the default branch name` を選択して **`main`** と入力 |
| Adjusting your PATH environment | `Git from the command line and also from 3rd-party software`（推奨）を選択 |
| Configuring line ending conversions | `Checkout Windows-style, commit Unix-style line endings` を選択 |
| その他の設定 | デフォルトのままでOK |

4. 「Install」をクリックし、完了後「Finish」をクリックする

### インストール確認

スタートメニューで「Git Bash」と検索して起動し、以下を入力する：

```
git --version
```

`git version 2.x.x` のようなバージョン番号が表示されれば成功。

### 初期設定（ユーザー名とメールアドレスの登録）

Git Bash で以下を実行する（`"..."` の中を**GitHubアカウントと同じ情報**に書き換えてください）：

```
git config --global user.name "Taro Yamada"
git config --global user.email "taro.yamada@example.com"
```

設定確認：

```
git config --global user.name
git config --global user.email
```

入力した情報が表示されればOK。

---

## 2. リポジトリのクローン（HP ファイル一式の取得）

「クローン」とは、GitHub 上にある HP のファイル一式を自分のPCにコピーする作業です。

> **事前に確認：** リポジトリへの push 権限が必要です。前任者に **GitHub の Collaborator への追加** を依頼してください。

### クローン手順

1. Git Bash を起動する
2. ファイルを保存したいフォルダに移動する（例：ユーザーフォルダ直下）：

```
cd /c/Users/（自分のユーザー名）
```

3. 以下のコマンドでクローンする：

```
git clone https://github.com/HirosawaLab/Homepage.git
```

4. `Homepage` フォルダが作成され、中にHPのファイルが入っていれば成功。

### 作業時に使う基本コマンド

```
# 作業開始前：GitHubの最新版を取得する（必ず最初に実行）
git pull

# 変更したファイルを確認する
git status

# 変更ファイルをステージングする（ファイル名を指定推奨）
git add News.html

# 変更を記録する（""の中に変更内容を書く）
git commit -m "News.html：4月の学会発表を追加"

# GitHubに送信する
git push
```

---

## 3. 大容量フォルダの取得（ギガファイル便）

`album/` と `oldsite/` はファイルサイズが大きいため GitHub では管理しておらず、ギガファイル便で共有しています。
パスワードは前任者からLINEで受け取った4桁の数字を使って取得してください。

> **パスワードはこのページには記載していません。前任者にLINEで確認してください。**

### ダウンロード手順

1. 以下のURLをブラウザで開く：
   https://87.gigafile.nu/0408-6c65e10c1dd0092b8d6c5a342f02c27a
2. パスワード入力欄に前任者からLINEで受け取った4桁の数字を入力する
3. 「ダウンロード」ボタンをクリックして `oldsite.zip` を保存する
4. ダウンロードした `oldsite.zip` を解凍する
   - Windowsの場合：`.zip` ファイルを右クリック →「すべて展開」→ 展開先を指定して「展開」

### フォルダの配置

`oldsite.zip` を解凍すると `album/` と `oldsite/` の2つのフォルダが入っています。
それぞれを HP フォルダ直下に配置する：

```
Homepage/
└── HP/
    ├── album/     ← oldsite.zip の中の album フォルダをここに置く
    ├── oldsite/   ← oldsite.zip の中の oldsite フォルダをここに置く
    ├── css/
    ├── js/
    └── ...
```

配置後、`album/` と `oldsite/` が HP フォルダ直下にあることを確認すれば完了。
これらのフォルダは `.gitignore` に登録されているため、誤って `git push` してしまう心配はありません。

---

## 4. Cursor のセットアップ

Cursor はVS Codeをベースにした、AIエージェントが使えるコードエディタです。

**公式サイト：** https://cursor.com

### インストール

1. https://cursor.com/download にアクセスする
2. PCに合わせてインストーラーを選ぶ（通常の64ビットPC → **Windows (x64) User**）
3. ダウンロードした `.exe` を実行し「Next」を押し続けて「Install」をクリックする
4. 完了後「Finish」をクリックすると Cursor が起動する

### アカウントのサインイン

1. 起動時にサインインを求められるので、**Sign up** からアカウントを作成する
   - Google・GitHub・メールアドレスで登録可能。クレジットカード不要。
   - 新規登録すると **7日間のPro無料トライアル** が自動付与される
2. サインイン後、VS Code の設定をインポートするか聞かれる場合がある（任意）

### HP フォルダを開く

1. Cursor を起動する
2. メニューバーの「File」→「Open Folder」をクリックする
3. クローンした HP フォルダ（例：`C:\Users\（ユーザー名）\Homepage\HP`）を選択する
4. 左側のファイルツリーに HP のファイル一覧が表示される

### ターミナルの設定（重要）

Cursor 内でコマンドを実行するとき、デフォルトの CMD では一部コマンドが動かないため、**Git Bash に変更する**。

1. `Ctrl + ,` で設定を開く
2. 検索欄に `terminal default` と入力する
3. 「Terminal > Integrated > Default Profile: Windows」を **Git Bash** に変更する

### Live Server 拡張機能のインストール

HTML を編集した結果をブラウザでリアルタイムに確認できます。

1. 左側サイドバーの「拡張機能」アイコンをクリックする（または `Ctrl+Shift+X`）
2. 検索ボックスに `Live Server` と入力する
3. 作者が「Ritwick Dey」の「Live Server」を「インストール」する
4. 完了すると画面下部のステータスバーに **「Go Live」** ボタンが表示される

**使い方：**

1. 確認したいHTMLファイル（例：`News.html`）を開く
2. 下部の **「Go Live」** をクリックする
3. ブラウザが自動で開いてプレビュー表示される
4. ファイルを保存（`Ctrl+S`）するとブラウザが自動リロードされる

> **注意：** ローカルプレビューと実際のサーバーで見た目が異なる場合があります。最終確認は必ずFileZillaでアップロードした後、実際のURLで行ってください。

---

## 5. Codex（AIエージェント）のセットアップ

Cursor に搭載されているAIエージェント（**Agent モード**）を使うことで、日本語で指示するだけでHTMLを自動的に編集できます。

> **Cursor のサインインが完了していれば、追加のAPIキー設定なしにすぐ使えます。**

### Agent モードの起動方法

1. Cursor 上で `Ctrl + I` を押す（Composerパネルが開く）
2. パネル上部にあるモード切替で **「Agent」** を選択する
3. 下部の入力欄に日本語で指示を入力して Enter を押す

| 操作 | ショートカット |
|---|---|
| Composer（Agent）を開く | `Ctrl + I` |
| AI Chat を開く | `Ctrl + L` |
| カーソル位置をインライン編集 | `Ctrl + K` |

### 使い方のポイント

- **具体的に指示する**ほど精度が上がる
  - 例：「News.html の `<ul>` の先頭に、日付2026年4月6日、カテゴリ「その他」、内容「研究室に新メンバーを迎えました」のニュース項目を追加して」
- 変更の提案が表示されたら、**Accept（承認）** または **Reject（却下）** で取捨選択できる
- 大きな変更を指示する前は必ず **`git commit` でバックアップをとること**（万が一の場合に元に戻せる）

### 料金について

| プラン | 料金 | AIエージェントの利用 |
|---|---|---|
| Hobby（無料） | $0/月 | 月ごとに制限あり（試しに使うには十分） |
| Pro | $20/月 | フルアクセス・大量利用可能 |

HP係の作業量であれば、無料プランで十分な場合が多いです。

---

## 6. FileZilla のインストール

FileZilla はFTPを使ってファイルをWebサーバーにアップロードするためのソフトウェアです。

**公式サイト：** https://filezilla-project.org

### インストール

1. https://filezilla-project.org にアクセスする
2. **「Download FileZilla Client」** をクリックする（**Server ではなく Client**）
3. 無料版のインストーラーをダウンロードする（**無料版で問題なし**）
   - ダウンロード中に「Sponsored offers」が出たら「Decline」でスキップ
4. ダウンロードした `.exe` を実行し「I Agree」→「Next」→「Install」→「Finish」

### サーバーへの接続情報の引継ぎ

FileZilla でサーバーに接続するには以下の情報が必要です。**前任者から受け取ってください。**

| 項目 | 内容 |
|---|---|
| ホスト（Host） | サーバーのアドレス |
| ユーザー名（Username） | FTPアカウントのユーザー名 |
| パスワード（Password） | FTPアカウントのパスワード |
| ポート（Port） | 21（FTP）または 22（SFTP） |

> **重要：** `docs/` フォルダと `prompt/` フォルダの内容は**絶対にアップロードしない**こと。内部管理用ファイルであり、公開してはいけません。

※ FileZilla の具体的な使い方は、実際の作業時に運用マニュアルを参照してください。

---

## 7. 運用マニュアルの熟読

HPの更新手順はGitHub上の `docs/knowledgebase.md` にまとめられています。事前に読んでおいてください。

**リンク：** https://github.com/HirosawaLab/Homepage/tree/main/HP/docs

特に以下の点を把握しておくこと：

- **更新パターン（P1〜）：** ニュース追加・メンバー追加・論文追加など、場面ごとの具体的な手順
- **ルール【B】：** 受賞系のニュースはアルバムページにコメントを追加する
- **ルール【G】：** 森野さんのページ（`info_morino.html`）は変更前に本人確認が必要
- **ルール【E】：** `docs/`・`prompt/` フォルダはFileZillaでアップロード禁止

---

## まとめ：ツールと用途

| ツール | 主な用途 |
|---|---|
| Git | ソースコードのバージョン管理・GitHubとの連携・バックアップ |
| Cursor | HTML/CSSの編集エディタ・ローカルプレビュー（Live Server） |
| Codex（Cursor Agent） | AIへの指示でHTMLを自動編集 |
| FileZilla | 編集したファイルをWebサーバーにアップロード |

*参考：[Git 公式](https://git-scm.com) / [Cursor 公式](https://cursor.com) / [FileZilla 公式](https://filezilla-project.org) / [運用マニュアル](https://github.com/HirosawaLab/Homepage/tree/main/HP/docs)*

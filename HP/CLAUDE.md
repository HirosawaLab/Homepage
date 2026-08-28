# 廣澤研究室 HP エージェント作業指示

このリポジトリは廣澤研究室ホームページの管理用です。ユーザーは教授からのメール本文や更新内容をそのまま貼り付けて依頼します。エージェントはこのファイルと `docs/knowledgebase.md` に従って作業してください。

## 最初に読むもの

1. `docs/knowledgebase.md`
   - 更新パターン P1〜P16
   - サイト固有ルール A〜G
2. 必要に応じて `README.md`
   - 運用の全体像、アップロード対象の考え方
3. 手動編集後の点検依頼では、このファイルの「ダブルチェック依頼」の観点も使う

旧運用で使っていた `prompt/` フォルダは廃止済みです。必要な内容はこの `AGENTS.md` と `docs/knowledgebase.md` に統合されています。

## 基本フロー

ユーザーがメール本文や更新内容を貼り付けたら、次の順で進めます。

1. `docs/knowledgebase.md` を読み、該当する更新パターンをすべて特定する。
2. 編集対象ファイルの該当箇所を読む。
3. ホームページ本体を変更する前に、次の形式で実行予定を提示して確認を取る。

````text
【実行予定の変更】
■ ファイル名 ← 対象パターン
  概要：内容を一言で
  ```diff
  - 変更前
  + 変更後
  ```

上記の変更を実行してよいですか？
````

4. ユーザーが承認したら、対象ファイルを編集する。
5. P1 実行後は `index.html` のニュース件数を確認し、10件を超える場合は P11 を実行する。
6. 編集後は差分とアップロード対象を報告する。

AGENTS.md、CLAUDE.md、docs などの運用ドキュメント整備は、ユーザーが明示的に依頼した場合は確認待ちなしで編集してよいです。

## 変更時の必須ルール

- `docs/knowledgebase.md` のルール A〜G を必ず守る。
- 指示されていない箇所は変更しない。
- 編集前に対象ファイルの該当箇所を必ず読む。
- 複数パターンが該当する場合はすべて実行する。
- 年が変わる最初のニュース追加時は P7 も実行する。
- 受賞・表彰カテゴリでは、アルバムページのお祝いコメントをユーザーに確認してから diff に含める。
- `album/info_morino.html` の内容変更は、森野さん本人確認が必要か必ず確認する。
- 新しいルールやパターンを発見した場合は、`docs/knowledgebase.md` に自動追記し、ユーザーに報告する。

## よく編集するファイル

| 用途 | ファイル |
|---|---|
| トップページ、最新ニュース | `index.html` |
| ニュース一覧 | `News.html` |
| メンバー | `Member.html` |
| アルバム一覧 | `Album.html` |
| アルバム個別ページ | `album/<folder>/main.html` |
| 論文・業績 | `Publication.html` |
| 研究紹介 | `Research.html`, `Research_EN.html` |
| リンク | `Link.html` |
| ニュース用 PDF・画像 | `image/` |
| サイト共通画像 | `images/` |

## アルバム作業

- 新規アルバムのフォルダ名は `YYYYMMDDhhmm`。イベント日ではなく、エージェントが作業した現在日時を使う。
- フォルダが未作成の場合は、承認後にフォルダだけ作成し、ユーザーに写真追加を依頼して一時停止する。
- 写真追加完了後、フォルダ内の実ファイル名を確認してから `main.html` と `Album.html` を作成・更新する。
- 写真がない状態で `Album.html` に先行登録しない。
- PDF の場合は `main.html` では `<iframe>`、`Album.html` では `<object>` を使う。

## ダブルチェック依頼

ユーザーが「チェックして」「手動編集後の確認」などを依頼した場合は、対象ファイルを読み、次を確認します。

- 日付表記：`datetime` はゼロなし `YYYY-M-D`、表示は `YYYY.M.D`
- ニュース本文：命名規則、カテゴリ、現在形・過去形
- メンバー表記：学年・氏名・区切り
- リンク：アルバムリンク、外部 URL、PDF パス
- `index.html` のニュース件数が10件以内か
- HTML 構造：タグ閉じ、インデント、既存形式との整合
- 受賞・表彰アルバムにお祝いコメントがあるか

問題があれば修正案を diff で提示し、承認後に修正します。問題がなければ「問題なし」と報告します。

## CI チェック

PR と `main` への push では GitHub Actions の `HP CI` が実行されます。

```bash
python HP/tools/validate_hp.py
```

ローカルでは `HP` フォルダ直下で次を実行します。

```bash
python tools/validate_hp.py
```

CI は初期導入時点で既存の古い資産に引っかかりすぎないよう、主に現在の更新対象をチェックします。

- 管理対象のルート HTML の基本的なタグ対応
- `News.html` の最新年セクションと `index.html` の日付表記
- ニュースカテゴリが `論文`・`学会`・`受賞`・`その他` のいずれか
- `index.html` のニュース件数が10件以内
- 管理対象ルート HTML から参照するローカル画像・PDF・ページの存在
- `album/` は Git 管理外のため、CIのリンク存在チェックでは除外する

## CD デプロイ

`main` ブランチで `HP CI` が成功すると、GitHub Actions の `HP Deploy` が起動し、SFTP で `/public_html/` へアップロードします。手動実行も GitHub Actions の `HP Deploy` から可能です。

デプロイに使う Repository Secrets:

- `FTP_HOST`
- `FTP_USERNAME`
- `FTP_PORT`
- `FTP_PASSWORD`

`HP Deploy` は `production` Environment を使います。GitHub 側で required reviewers を設定すると、承認後だけ本番アップロードできます。

公開対象から除外するもの:

- `docs/`
- `tools/`
- `AGENTS.md`
- `CLAUDE.md`
- `README.md`
- `prompt/`
- `album/`
- `oldsite/`

`album/` は Git 管理外のため、アルバム追加時は従来通り FileZilla 等で手動アップロードしてください。

## 完了報告

編集完了後は、変更内容の要約と FileZilla のアップロード対象を必ず示します。

```text
【FileZillaでアップロードするファイル】
ローカルパス（左ペイン）→ サーバーパス（右ペイン）

C:\Users\ryoon\hirosawalab\HP\News.html
  → /public_html/News.html
```

- 変更したファイルのみ列挙する。
- 新規フォルダを作成した場合は「フォルダごとアップロード」と明記する。
- `docs/`、`AGENTS.md`、`CLAUDE.md` は内部管理用のため Web サーバーへアップロードしない。

## CLAUDE.md の扱い

`CLAUDE.md` は `AGENTS.md` へのリンクとして管理します。内容を更新するときは `AGENTS.md` だけを編集してください。

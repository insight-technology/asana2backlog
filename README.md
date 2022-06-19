# asana2backlog

## 実行方法

```
python3 asana2backlog.py <asana_project_id> <asana_pat> <backlog_space_name> <backlog_api_key> <backlog_project_key>
```

* <asana_project_id>: AsanaのProject ID
* <asana_pat>: AsanaのPersonal Access Token

* <backlog_space_name>: BacklogのSpace name
* <backlog_api_key>: BacklogのAPI key
* <backlog_project_key>: BacklogのProject key

## 注意点

* ユーザーのマッピング

Asanaの指定プロジェクトが属するworkspaceのユーザー一覧と、Backlogの指定プロジェクト内のユーザー一覧とを、メールアドレスで突き合わせます。

* 優先度、カテゴリー、その他のカスタムフィールド

pybacklogpyに状態の一覧を取得するAPIのラッパーがないので、何らかの設定を行いたい場合は状態取得のところだけ自分でcurlか何かで実行して移行先のidを取得してください。(設定しなければ未着手になるようです。)(Create status mapping)
https://developer.nulab.com/ja/docs/backlog/api/2/get-status-list-of-project/#

優先度はasanaのカスタム属性で使用していたものがあればそれに合わせて設定しています。設定しなければ中になるので適当にコード修正してください。(Create priority mapping)

単純なマッピングは難しいので適当にコードを修正しての対応が必要です。(Create custom field mapping, set custom fieldsあたり)
設定すべきカスタムフィールドのプロパティ名も適当に探して設定してください。

* sub task (課題の親子)

Asanaのサブタスクは、子課題にしています。Asanaではサブタスクのサブタスクも設定できますが、Backlogでは子供の子供は設定できないようなので、全て最初の親課題に紐づけています。

* taskの依存関係

AsanaでのTaskの依存関係はBacklogには該当するものがないようなので引き継ぎません。

* taskの開始日

Asanaには該当するものがないようなので設定されません。

* 添付ファイル

スクリプトを実行しているカレントディレクトリにダウンロードし、その後アップロードします。アップロード後はファイルを削除します。ファイル名が100文字を超えているとアップロードできないのでエラー出力します。その場合は適当に手でアップロードするなどしてください。エラー出力した場合はファイルは削除しません。

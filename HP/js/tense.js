/**
 * tense.js
 * <time datetime="YYYY-M-D"> の日付が過去になったら、
 * <p> 内のテキストを自動で過去形に変換する。
 *
 * 【使い方】
 * 1. 通常は自動変換ルール（下記 AUTO_RULES）が適用される
 *    例: 「で発表します」→「で発表しました」
 *
 * 2. 自動変換では対応できない場合、<p> に data-past 属性で
 *    過去形テキストを直接指定できる（HTMLタグ使用可）:
 *    <p data-past="公開セミナーが開催されました">公開セミナー　参加者募集</p>
 */

(function () {
  // 自動変換ルール: [正規表現, 置換後テキスト]
  // 上から順に適用されるため、長いパターンを先に書く
  var AUTO_RULES = [
    [/する予定です/g, 'しました'],
    [/する予定/g,     'した'],
    [/予定です/g,     '行われました'],
    [/します/g,       'しました'],
    [/でます/g,       'でました'],
    [/ます/g,         'ました'],
    [/参加者募集/g,   '開催されました'],
    [/募集中/g,       '終了しました'],
  ];

  document.addEventListener('DOMContentLoaded', function () {
    var today = new Date();
    today.setHours(0, 0, 0, 0);

    document.querySelectorAll('li').forEach(function (li) {
      var timeEl = li.querySelector('time[datetime]');
      if (!timeEl) return;

      var datetimeStr = timeEl.getAttribute('datetime');

      // "YYYY-M-D" 形式を抽出（"2026-2-21" や "2025-11.7-9" にも対応）
      var m = datetimeStr.match(/(\d{4})-(\d{1,2})[.\-](\d{1,2})/);
      var eventDate;
      if (m) {
        eventDate = new Date(parseInt(m[1]), parseInt(m[2]) - 1, parseInt(m[3]));
      } else {
        // 日が取れない場合は年月のみで判定
        var m2 = datetimeStr.match(/(\d{4})-(\d{1,2})/);
        if (!m2) return;
        eventDate = new Date(parseInt(m2[1]), parseInt(m2[2]) - 1, 1);
      }

      // 未来・当日はスキップ
      if (eventDate >= today) return;

      var p = li.querySelector('p');
      if (!p) return;

      // data-past 属性が指定されていればそちらを優先
      if (p.dataset && p.dataset.past) {
        p.innerHTML = p.dataset.past;
        return;
      }

      // 自動変換ルールを適用
      var html = p.innerHTML;
      AUTO_RULES.forEach(function (rule) {
        html = html.replace(rule[0], rule[1]);
      });
      p.innerHTML = html;
    });
  });
})();

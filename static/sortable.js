// Sortable list groups. A <ul class="sortable-list" data-default-sort="key">
// holds one <li class="sort-header"> with [data-sort-key] links, and
// <li class="sort-row"> rows carrying the values as data-sort-<key>.
// Links with data-sort-type="text" sort alphabetically, the rest numerically.
// Clicking the current column again reverses the order.
$(function() {
  $('.sortable-list').each(function() {
    var $list = $(this);
    var $header = $list.children('.sort-header');
    var key = null;
    var desc = true;

    function value(row, isText) {
      var v = $(row).attr('data-sort-' + key) || '';
      return isText ? v : (parseFloat(v) || 0);
    }

    function sortBy(newKey) {
      var isText = $header.find('[data-sort-key="' + newKey + '"]').data('sort-type') === 'text';
      if (newKey === key) {
        desc = !desc;
      } else {
        key = newKey;
        desc = !isText;
      }

      var rows = $list.children('.sort-row').get();
      rows.sort(function(a, b) {
        var x = value(a, isText), y = value(b, isText);
        var c = isText ? x.localeCompare(y) : x - y;
        return desc ? -c : c;
      });
      $list.append(rows);

      $header.find('.sort-arrow').text('');
      $header.find('[data-sort-key="' + key + '"] .sort-arrow').text(desc ? ' ▼' : ' ▲');
    }

    $header.on('click', '[data-sort-key]', function(e) {
      e.preventDefault();
      sortBy($(this).data('sort-key'));
    });

    sortBy($list.data('default-sort'));
  });
});

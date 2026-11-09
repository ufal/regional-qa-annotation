// "Show times" switch on the admin pages: shows or hides the time statistics
$(function() {
  $('#show-times').change(function() {
    $('.stat-time').toggleClass('d-none', !$(this).is(':checked'));
  });
});

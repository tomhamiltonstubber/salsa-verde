$(document).ready(() => {
  // try {
  //   $('select').not('.select2-offscreen').not('[id*=__prefix__]').select2({allowClear: true, placeholder: '---------'})
  // } catch (e) {
  //   this seems to happen occasionally when something has gone wrong, ignore it
  // }
  const icons = {
    time: 'fa fa-clock',
    date: 'fa fa-calendar',
    up: 'fa fa-chevron-up',
    down: 'fa fa-chevron-down',
    previous: 'fa fa-chevron-left',
    next: 'fa fa-chevron-right',
    today: 'fa fa-square',
    clear: 'fa fa-trash',
    close: 'fa fa-remove'
  }
  $('.date-time-picker').each((i, el) => {
    const $el = $(el)
    $el.datetimepicker({icons: icons, format: $el.find('input').data('format')})
  })
})

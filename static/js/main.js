$(document).ready(() => {
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
    const $input = $el.find('input')
    const $init = $('#initial-' + $input.attr('id'))
    $el.datetimepicker({
      icons: icons,
      format: $input.data('format'),
      date: $init.val(),
    })
  })
  init_confirm_follow()
  if ($('#order-list').length) {
    init_ef_form()
  }
  init_select2()
  init_formsets()
})

function init_select2 () {
  try {
    $('select').not('.select2-offscreen').not('[id*=__prefix__]').select2({allowClear: true, placeholder: '---------'})
  } catch (e) {
    // this seems to happen occasionally when something has gone wrong, ignore it
  }
}

function init_confirm_follow () {
  const $el = $(document)
  $el.find('[data-confirm]').click(function (e) {
    let $a = $(this)
    const target = $a.attr('target')
    let link = $a.attr('href')
    let method = $a.data('method') || 'POST'
    e.preventDefault()
    bootbox.confirm({
      message: $a.data('confirm'),
      title: $a.data('confirm-title') || null,
      callback: result => {
        if (result) {
          if (method.toLowerCase() === 'post') {
            let form = $('#post-form')
            form.attr('action', link)
            $.each($a.data(), function (k, v) {
              if (k === 'method') {
                return
              }
              $('<input>').attr({
                type: 'hidden',
                name: k,
                value: v
              }).appendTo(form)
            })
            if (target) {
              window.open(link, target)
            } else {
              form.submit()
            }
          } else {
            document.location.href = link
          }
        }
      }
    })
  })

  $('[data-method="POST"]').not('[data-confirm]').not('.no-submit').click(function (e) {
    const $a = $(this)
    const link = $a.attr('href')
    e.preventDefault()
    if (link === '#') {
      return
    }
    const form = $('#post-form')
    form.attr('action', link)
    for (const [key, value] of Object.entries($a.data())) {
      if (key !== 'method') {
        $('<input>').attr({type: 'hidden', name: key, value: value}).appendTo(form)
      }
    }
    form.submit()
  })
}

function reset_choices ($select, choices) {
  $select.empty()
  $.each(choices, (k, v) => {
    $select.append($('<option></option>').attr('value', k).text(v))
  })
  $select.select2()
}

function init_ef_form() {
  const $county = $('#id_county')
  const $region = $('#id_region')
  const check_county_choices = v => {
    if (v === 'NORTH IRELAND') {
      reset_choices($county, window.ni_counties)
    } else {
      reset_choices($county, window.ie_counties)
    }
  }
  $region.change(function () {
    check_county_choices($(this).val())
  })
  check_county_choices($region.val())
}

function init_formsets () {
  $('.formsets-form .formset-form').each((i, el) => {
    $(el).formset({
      formTemplate: '#id_empty_' + el.dataset.formset_id,
      addCssClass: 'btn btn-default',
      deleteCssClass: 'btn btn-danger',
      addText: 'Add another',
      deleteText:'Remove',
      prefix: el.dataset.prefix,
      added: () => {
        init_select2()
        hide_extra_buttons()
      },
    })
    let hide_buttons_declared = false

    const hide_extra_buttons = () => {
      if (!hide_buttons_declared) {
        $('.dynamic-form').each((i, el) => {
          const $els = $(el).find('.btn-danger')
          if ($els.length === 2) {
            $($els[0]).hide()
          }
        })
        hide_buttons_declared = true
      }
    }
    hide_extra_buttons()
  })
}

$(document).ready(() => {
  $('.date-time-picker').each((i, el) => {
    const $el = $(el)
    const $input = $el.find('input')
    const $init = $('#initial-' + $input.attr('id'))
    new tempusDominus.TempusDominus(el, {
      defaultDate: new Date(Date.parse($init.val())),
    })
  })

  init_confirm_follow()
  if ($('#ef-form').length) {
    init_ef_form()
  }
  init_select2()
  init_formsets()

  const package_formsets = $('.formset-packages-sending')
  if (package_formsets.length > 0) {
    const id_regex = /\d/g;
    package_formsets.each((i, el) => {
      let package_type = $(el).find('select[data-field-id="package-type"]')[0]
      $(package_type).change(function () {
        const pu_deets = window.pack_temp_lu[$(this).val()]
        if (pu_deets) {
          let form_index = package_type.id.match(id_regex)[0]
          $(`#id_form-${form_index}-length`).val(pu_deets['length'])
          $(`#id_form-${form_index}-width`).val(pu_deets['width'])
          $(`#id_form-${form_index}-height`).val(pu_deets['height'])
          $(`#id_form-${form_index}-weight`).val(pu_deets['weight'])
        }
      })
    })
  }
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
      addCssClass: 'btn btn-outline-primary',
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

$(document).ready(() => {

  init_confirm_follow()
  if ($('#ef-form').length) {
    init_ef_form()
  }
  init_select2()
  init_dt_pickers()
  init_formsets()
  init_input_groups()
  init_product_add_form()

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

function init_dt_pickers() {
  $('.date-time-picker').each((i, el) => {
    const $el = $(el)
    const $input = $el.find('input')
    const $init = $('#initial-' + $input.attr('id'))
    new tempusDominus.TempusDominus(el, {
      defaultDate: new Date(Date.parse($init.val())),
      localization: {
        format: 'dd/MM/yyyy HH:mm'
      }
    })
    $el.click().click()
  })
}

function init_select2 () {
  try {
    $('select').not('.select2-offscreen').not('[id*=__prefix__]').select2({allowClear: true, placeholder: '---------', theme: 'bootstrap-5'})
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
  $select.select2({theme: 'bootstrap-5'})
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

function init_input_groups () {
  const $inputs = $('input[input-group-label-lu]')
  $inputs.each((i, el) => {
    const $el = $(el)
    // We need to add the 'input-group' class to the parent div and append the span with class input-group text to it
    const $parent = $el.parent()
    $parent.addClass('input-group')
    const $span = $('<span>').addClass('input-group-text').text('Units')
    $span.appendTo($parent)

    const id_label_lu = JSON.parse($el.attr($el.attr('input-group-label-lu')))
    const linked_input = $('#' + $el.attr('linked-input-id'))
    linked_input.change(() => {
      $span.text(id_label_lu[linked_input.val()] + 's')
    })
  })
}

function init_product_add_form() {
  const $product_type = $('#id_product_type')
  if ($product_type.length === 0) {
    return
  }
  const $spinner = $('#spinner')
  const $product_ingredients = $('#product-ingredients')
  $product_type.change(function () {
    $spinner.show()
    $product_ingredients.empty()

    const data_url = $(this).attr('product-ingredient-choices-url-template').replace('999', this.value)
    $.getJSON(data_url, function (data) {
      $.each(data, function (i, ingred_data) {
        const unit_str = ingred_data['unit']
        const ingred_choices = ingred_data['choices']
        const name = ingred_data['name']

        const $new_row = $('<div class="row"></div>')

        const $ingredient_col_wrapper = $('<div></div>').attr('class', 'col')
        const $ingredient_wrapper = $('<div></div>').attr('class', 'form-group')

        const $ingred_label = $('<label></label>').attr('for', `id_ingredient_${i}`).text(name).addClass("required control-label")
        $ingred_label.appendTo($ingredient_wrapper)

        const $new_ingredient_select = $('<select></select>')
          .attr('name', `ingredient_${i}`)
          .attr('class', 'form-control')
          .attr('id', `id_ingredient_${i}`)
          .attr('required', 'required')

        $new_ingredient_select.appendTo($ingredient_wrapper)
        $ingredient_wrapper.appendTo($ingredient_col_wrapper)
        $ingredient_col_wrapper.appendTo($new_row)

        $.each(ingred_choices, function (i, opt) {
          $new_ingredient_select.append($('<option></option>').attr('value', opt[0]).text(opt[1]))
        })

        const $quantity_col_wrapper = $('<div></div>').attr('class', 'col')
        const $quantity_wrapper = $('<div></div>').attr('class', 'form-group')

        const $quantity_label = $('<label></label>').attr('for', `id_ingredient_quantity_${i}`).text('Quantity').addClass("required control-label")
        $quantity_label.appendTo($quantity_wrapper)

        const $quantity_input_wrapper = $('<div></div>').attr('class', 'input-group')
        const $quantity_input = $('<input></input>')
          .attr('type', 'number')
          .attr('name', `ingredient_quantity_${i}`)
          .attr('class', 'form-control')
          .attr('id', `id_ingredient_quantity_${i}`)
          .attr('placeholder', 'Quantity')
          .attr('step', '0.01')
          .attr('required', 'required')
        $quantity_input.appendTo($quantity_input_wrapper)
        const $quantity_unit = $('<span></span>').attr('class', 'input-group-text').text(unit_str)
        $quantity_unit.appendTo($quantity_input_wrapper)
        $quantity_input_wrapper.appendTo($quantity_wrapper)
        $quantity_wrapper.appendTo($quantity_col_wrapper)
        $quantity_col_wrapper.appendTo($new_row)

        $new_row.appendTo($product_ingredients)
      })
      init_select2()
      $spinner.hide()
    })
  })
  $product_type.change()
}

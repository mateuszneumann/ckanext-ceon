/* Module for working with ancestral lincense field inputs.
 */
this.ckan.module('ancestral-fields', function (jQuery, _) {
  return {
    options: {
      /* The selector used for each author field wrapper */
      fieldSelector: '.control-ancestral'
    },

    /* Initializes the module and attaches author event listeners. This
     * is called internally by ckan.module.initialize().
     *
     * Returns nothing.
     */
    initialize: function () {
      jQuery.proxyAll(this, /_on/);
      var master = this;
      var radios = this.options.fieldSelector + ' input[type="radio"]';
      $(radios).each(function(index) {
        var r = $(radios)[index];
        $(r).on('change', master._onChange);
      });
    },

    /* Event handler that fires when the last key in the author field block
     * changes.
     */
    _onChange: function (event) {
      console.log(event.target);
      var ancestral_div = this.options.fieldSelector + ' #s2id_field-ancestral_license';
      var ancestral_select = this.options.fieldSelector + ' #field-ancestral_license';
      /*
      if ((event.target.value == 'on') && (event.target.is(":checked"))) {
        $(ancestral_div).prop('disabled', 'disabled');
        $(ancestral_select).prop('disabled', 'disabled');
      } else if ((event.target.value == 'off') && (event.target.is(":checked"))) {
        $(ancestral_div).prop('disabled', false);
        $(ancestral_select).prop('disabled', false);
      }
      */
      if (event.target.value == 'off') {
        $(ancestral_div).prop('disabled', 'disabled');
        $(ancestral_select).prop('disabled', 'disabled');
      } else if (event.target.value == 'on') {
        $(ancestral_div).prop('disabled', false);
        $(ancestral_select).prop('disabled', false);
      }
    },

  };
});

/* Module for working with multiple author field inputs. This will create
 * a new field when the user enters text into the last field key. It also
 * gives a visual indicator when fields are removed by disabling them.
 *
 * See the snippets/custom_form_fields.html for an example.
 */
this.ckan.module('authors-fields', function (jQuery, _) {
  return {
    options: {
      /* The selector used for each author field wrapper */
      fieldSelector: '.control-custom'
    },

    /* Initializes the module and attaches author event listeners. This
     * is called internally by ckan.module.initialize().
     *
     * Returns nothing.
     */
    initialize: function () {
      if (!jQuery('html').hasClass('ie7')) {
        jQuery.proxyAll(this, /_on/);

        var delegated = this.options.fieldSelector + ':last input:first';
        this.el.on('change', delegated, this._onChange);
        this.el.on('change', ':checkbox', this._onRemove);

        // Style the remove checkbox like a button.
        this.$('.checkbox').addClass("btn btn-danger icon-remove");
      }
    },

    /* Creates a new field and appends it to the list. This currently works by
     * cloning and erasing an existing input rather than using a template. In
     * future using a template might be more appropriate.
     *
     * element - Another author field element to wrap.
     *
     * Returns nothing.
     */
    newField: function (element) {
      this.el.append(this.cloneField(element));
    },

    /* Clones the provided element, wipes it's content and increments it's
     * for, id and name fields (if possible).
     *
     * current - An author field to clone.
     *
     * Returns a newly created author field element.
     */
    cloneField: function (current) {
      return this.resetField(jQuery(current).clone());
    },

    /* Wipes the contents of the field provided and increments it's name, id
     * and for attributes.
     *
     * field - An author field to wipe.
     *
     * Returns the wiped element.
     */
    resetField: function (field) {
      function increment(index, string) {
        return (string || '').replace(/\d+/, function (int) { return 1 + parseInt(int, 10); });
      }

      var input_position = field.find('input[name$="_position"]');
      var position = parseInt(input_position.val(), 10);

      var input = field.find(':input');
      input.val('').attr('id', increment).attr('name', increment);

      var label = field.find('label');
      label.text(increment).attr('for', increment);

      input_position.val(1 + position);

      return field;
    },

    /* Disables the provided field and input elements. Can be re-enabled by
     * passing false as the second argument.
     *
     * field   - The field to disable.
     * disable - If false re-enables the element.
     *
     * Returns nothing.
     */
    disableField: function (field, disable) {
      field.toggleClass('disabled', disable !== false);
    },

    /* Event handler that fires when the last key in the author field block
     * changes.
     */
    _onChange: function (event) {
      if (event.target.value !== '') {
        var parent = jQuery(event.target).parents(this.options.fieldSelector);
        this.newField(parent);
      }
    },

    /* Event handler called when the remove checkbox is checked */
    _onRemove: function (event) {
      var parent = jQuery(event.target).parents(this.options.fieldSelector);
      this.disableField(parent, event.target.checked);
    }
  };
});

/* An funding-fields module for select elements that works just like
 * an autocomplete module (which was a starting point for writing this
 * code).
 *
 * See the modules/autocomplete.js for original source code.
 */
this.ckan.module('funding-fields', function (jQuery, _) {
  return {
    options: {
      tags: false,
      key: false,
      label: false,
      items: 10,
      source: null,
      interval: 1000,
      dropdownClass: '',
      containerClass: '',
      i18n: {
        noMatches: _('No matches found'),
        emptySearch: _('Start typing…'),
        inputTooShort: function (data) {
          return _('Input is too short, must be at least one character')
          .ifPlural(data.min, 'Input is too short, must be at least %(min)d characters');
        }
      }
    },


    /* Sets up the module, binding methods, creating elements etc. Called 
     * internally by ckan.module.initialize(); 
     * 
     * Returns nothing. 
     */
    initialize: function () {
      jQuery.proxyAll(this, /_on/, /format/);
      var choices = this.el.attr('data-select').split('|');
      var selected = this.el.val();
      this.setupAutoComplete(selected, choices);
      this.el.val(selected);
    },

    /* Sets up the auto complete plugin.
     *
     * Returns nothing.
     */
    setupAutoComplete: function (selected, choices) {
      var settings = {
        width: 'resolve',
        placeholder: " ",
        initSelection: function (element, callback) {
          var value = $(element).val();
          if (value)
              callback({ id: value, text: value });
        },

        query: function (query) {
          // match
          var items = $.grep(choices, function (item) {
            if (!query.term) {
              return true;
            } else {
              return query.matcher(query.term, item);
            }
          });
          items = items.sort();
          if (query.term) {
            items.push(query.term);
          }
          // map to {id: '', text: ''}
          var data = {};
          data.results = $.map(items, function (item) {
            return { id: item, text: item };
          })
          query.callback(data);                 
        },

      };

      // Different keys are required depending on whether the select is
      // tags or generic completion.
      if (!this.el.is('select')) {
        if (!this.options.tags) {
          settings.createSearchChoice = this.formatTerm;
        }
      }
      else {
        if (/MSIE (\d+\.\d+);/.test(navigator.userAgent)) {
          var ieversion=new Number(RegExp.$1);
          if (ieversion<=7) {return}
        }
      }

      var select2 = this.el.select2(settings).data('select2');

      if (this.options.tags && select2 && select2.search) {
        // find the "fake" input created by select2 and add the keypress event.
        // This is not part of the plugins API and so may break at any time.
        select2.search.on('keydown', this._onKeydown);
      }
      
      // This prevents Internet Explorer from causing a window.onbeforeunload
      // even from firing unnecessarily
      $('.select2-choice', select2.container).on('click', function() {
        return false;
      });
      this._select2 = select2;
      this.el.select2('val', selected);
    },

    /* Takes a string and converts it into an object used by the select2 plugin.
     *
     * term - The term to convert.
     *
     * Returns an object for use in select2.
     */
    formatTerm: function (term) {
      term = jQuery.trim(term || '');
      // Need to replace comma with a unicode character to trick the plugin
      // as it won't split this into multiple items.
      return {id: term.replace(/,/g, '\u002C'), text: term};
    },

    /* Callback function that parses the initial field value.
     *
     * element  - The initialized input element wrapped in jQuery.
     * callback - A callback to run once the formatting is complete.
     *
     * Returns a term object or an array depending on the type.
     */
    formatInitialValue: function (element, callback) {
      var value = jQuery.trim(element.val() || '');
      var formatted = jQuery.map(value.split("|"), this.formatTerm);

      // Select2 v3.0 supports a callback for async calls.
      if (typeof callback === 'function') {
        callback(formatted);
      }
      return formatted;
    },

  };
});

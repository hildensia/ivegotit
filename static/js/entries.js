/**
 * Created by johannes on 7/13/15.
 */
function removeEntry(list_id, entry_id) {
    $.post('/entry/rm', {
        gi_list: list_id,
        entry_id: entry_id
    }).done(function(removedEntry) {
        //$('#wait').hide();
        //$('#add-sign').show();
        $('#entry' + entry_id).slideUp(function() {
            $('#entry' + entry_id).remove();
        });
    }).fail(function() { });
}

function addEntry(list_id, entry) {
    $.post('/entry/add', {
        gi_list: list_id,
        entry: entry
    }).done(function(addedEntry) {
        $("#add-entry").before(addedEntry['html']);
        $("#newentry").val('');
        $("#entry"+addedEntry['entry_id']).hide();
        $("#entry"+addedEntry['entry_id']).slideDown();
    }).fail(function() { });
}

function replaceEntry(fnc, list_id, entry_id) {
    $.post(fnc, {
        gi_list: list_id,
        entry_id: entry_id
    }).done(function(gotit_Entry) {
        $('#entry' + entry_id).fadeOut("fast", function(){
            $(this).replaceWith(gotit_Entry['html']);
            $('#entry' + entry_id).hide().fadeIn("fast");
        });
    }).fail(function() { });
}

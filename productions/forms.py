import re
from django import forms
from models import Production, Part
from people.models import Person
from fields import PrettyDateField
from django.forms.formsets import BaseFormSet
from search.views import search_people
from common.templatetags.prettify import prettify

class CastCrewNullBooleanSelect(forms.widgets.NullBooleanSelect):
    def __init__(self, attrs=None):
        choices = ((u'1', 'Unknown'), (u'2', 'Cast'), (u'3', 'Crew'))
        super(forms.widgets.NullBooleanSelect, self).__init__(attrs, choices)

class ProductionEditForm(forms.ModelForm):
    last_modified = forms.DateTimeField(widget=forms.HiddenInput(), required=False)
    press_date = PrettyDateField()
    description = forms.CharField(required=False, widget=forms.Textarea(attrs={'cols': 30, 'rows':5}))

    class Meta:
        model = Production
        exclude = ('parts', 'created_by')

    def __init__(self, last_modified=None, *args, **kwargs):
        self.db_last_modified = last_modified
        kwargs['initial'] = { 'last_modified': last_modified }
        super(ProductionEditForm, self).__init__(*args, **kwargs)

    def clean(self):
        super(ProductionEditForm, self).clean()

        # Not clean_last_modified, as I want it as a generic error
        last_mod = self.cleaned_data.get('last_modified')
        if last_mod < self.db_last_modified:
            raise forms.ValidationError('I am afraid that this production has been edited since you started editing.')

        return self.cleaned_data

class PartAddForm(forms.ModelForm):
    person = forms.CharField()

    class Meta:
        model = Part
        exclude = ('production', 'credit', 'created_by', 'visible')

    def __init__(self, *args, **kwargs):
        super(PartAddForm, self).__init__(*args, **kwargs)
        self.fields['order'].widget.attrs['size'] = 5
        self.fields['cast'].widget = CastCrewNullBooleanSelect()

# person is the ext box where someone enters a name, and always will be
# person_choice is the selection of someone from that, or the creation of a new person
class PartEditForm(PartAddForm):
    id = forms.IntegerField(widget=forms.HiddenInput())
    person_choice = forms.ChoiceField(label='Person', widget=forms.RadioSelect(), required=False)
#    last_modified = forms.DateTimeField(widget=forms.HiddenInput())

    class Meta:
        model = Part
        fields = ('id', 'person_choice', 'person', 'role', 'cast', 'order', 'start_date', 'end_date')

    def __init__(self, last_modified=None, *args, **kwargs):
#        self.db_last_modified = last_modified
#        kwargs.setdefault('initial', {}).update({'last_modified':last_modified})
        super(PartEditForm, self).__init__(*args, **kwargs)
        if 'person_choice' in self.data and 'person' in self.data:
            choices = self.radio_choices(self.data['person'])
            self.fields['person_choice'].choices = choices

    def radio_choices(self, s):
        people, dummy = search_people(s)
        choices = []
        for p in people:
            last_production = p.productions.order_by('-IFNULL(press_date, IF(productions_production.end_date!="", productions_production.end_date, productions_production.start_date))')[0]
            choices.append( (p.id, prettify(str(p) + ', last in ' + str(last_production)) ) )
        if len(choices) > 1:
            choices.append( ( 'new', prettify('None of these, a new person called \'' + s + '\'') ) )
        else:
            choices.append( ( 'new', prettify('A new person called \'' + s + '\'') ) )
        choices.append( ( 'back', 'I misspelled, and will enter a new name below:' ) )
        return choices

    def clean(self):
        if 'person_choice' in self.cleaned_data:
            self.cleaned_data['person'] = self.cleaned_data['person_choice']
            del self.cleaned_data['person_choice']
        return self.cleaned_data

    def clean_person_choice(self):
        person = self.cleaned_data['person_choice']
        if re.match('[0-9]+$', person):
            return Person.objects.get(id=person)

        raise forms.ValidationError('Please select one of the choices below:')
        return person

    def clean_person(self):
        if not 'person' in self.changed_data:
            # The person hasn't altered, so use the Person object we already know about
            return self.instance.person

        person = self.cleaned_data['person']
        if not self.fields['person_choice'].choices:
            # Okay, so we have a search string
            choices = self.radio_choices(person)
            self.fields['person_choice'].choices = choices # = forms.ChoiceField( label='Person', choices=choices, widget = forms.RadioSelect() )
        return self.cleaned_data['person']

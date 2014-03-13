from django.dispatch import Signal
from django import forms

# Define signals used throughout the program to notify bots of actions to be taken
bidding_needed = Signal()
playing_needed = Signal()
collection_needed = Signal()


# Custom ModelChoiceField classes to not evaluate queries all the time
class LazyModelChoiceIterator(forms.models.ModelChoiceIterator):
    """
    note that only line with # *** in it is actually changed
    
    """
    
    def __iter__(self):
        if self.field.empty_label is not None:
            yield (u"", self.field.empty_label)
        if self.field.cache_choices:
            if self.field.choice_cache is None:
                self.field.choice_cache = [
                    self.choice(obj) for obj in self.queryset.all()
                ]
            for choice in self.field.choice_cache:
                yield choice
        else:
            for obj in self.queryset: # ***
                yield self.choice(obj)


class LazyModelChoiceField(forms.ModelChoiceField):
    """
    only purpose of this class is to call another ModelChoiceIterator
    
    """
    def _get_choices(self):
        if hasattr(self, '_choices'):
            return self._choices

        return LazyModelChoiceIterator(self)

    choices = property(_get_choices, forms.ModelChoiceField._set_choices)
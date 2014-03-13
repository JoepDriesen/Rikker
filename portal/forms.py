from django import forms
from portal.models import Bid
from django.contrib.auth import get_user_model
from portal import LazyModelChoiceField

class StartGameForm(forms.Form):
    
    player1 = LazyModelChoiceField(queryset=None, required=False)
    player2 = LazyModelChoiceField(queryset=None, required=False)
    player3 = LazyModelChoiceField(queryset=None, required=False)
    
    def __init__(self, *args, **kwargs):
        """
        To make sure the queryset is only evaluated once for every instance of the form, but updated every time
        a new instance is created
        
        """        
        all_users_no_bots = get_user_model().objects.exclude(is_bot=True)
    
        self.base_fields['player1'].queryset = all_users_no_bots
        self.base_fields['player2'].queryset = all_users_no_bots
        self.base_fields['player3'].queryset = all_users_no_bots
        
        return super(StartGameForm, self).__init__(*args, **kwargs)
    
    def get_players_to_invite(self):
        players = []
        if 'player1' in self.cleaned_data and self.cleaned_data['player1'] is not None:
            players.append(self.cleaned_data['player1'])
        if 'player2' in self.cleaned_data and self.cleaned_data['player2'] is not None:
            players.append(self.cleaned_data['player2'])
        if 'player3' in self.cleaned_data and self.cleaned_data['player3'] is not None:
            players.append(self.cleaned_data['player3'])
        return players
    
class MakeBidForm(forms.ModelForm):
    class Meta:
        model = Bid
        fields = ['bid']

class PickTrumpSuitAndMateForm(forms.ModelForm):
    # TODO: make all fields required
    class Meta:
        model = Bid
        fields = ['trump_suit', 'mate_suit']

class PickTrumpSuitForm(forms.ModelForm):
    # TODO: make all fields required
    class Meta:
        model = Bid
        fields = ['trump_suit']
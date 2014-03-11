from django import forms
from portal.models import Bid
from django.contrib.auth import get_user_model

class StartGameForm(forms.Form):
    
    player1 = forms.ModelChoiceField(queryset=get_user_model().objects.exclude(is_bot=True), required=False)
    player2 = forms.ModelChoiceField(queryset=get_user_model().objects.exclude(is_bot=True), required=False)
    player3 = forms.ModelChoiceField(queryset=get_user_model().objects.exclude(is_bot=True), required=False)
    
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
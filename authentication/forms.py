from django import forms
from django.contrib.auth import get_user_model
from django.utils.translation import ugettext_lazy as _

class RegistrationForm(forms.ModelForm):
    """
    Form for registering a new user account.
    
    """
    class Meta:
        model = get_user_model()
        fields = ['username', 'password']
    
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'required'}, render_value=False),
                               label=_("Password"),)
    
    password2 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'required'}, render_value=False),
                                label=_("Password (again)"),
                                help_text=_('Please enter the same password as above for verification purposes.'))
    
    def clean(self):
        """
        Verifiy that the values entered into the two password fields
        match. Note that an error here will end up in
        ``non_field_errors()`` because it doesn't apply to a single
        field.
        
        """
        super(RegistrationForm, self).clean()
        if 'password' in self.cleaned_data and 'password2' in self.cleaned_data:
            if self.cleaned_data['password'] != self.cleaned_data['password2']:
                raise forms.ValidationError(_("The two password fields didn't match."))
        return self.cleaned_data
    
    def save(self):
        return get_user_model().objects.create_user(username=self.cleaned_data['username'], password=self.cleaned_data['password'])

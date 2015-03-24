import mock
import nose
from restpy.fields import Field, FieldSet


def test_field_init():
    f = Field(setting1=1, setting2=2, required=True)
    assert f._name is None
    assert f._settings == {'setting1': 1, 'setting2': 2}
    assert f.required


def test_feld_init_not_required():
    f = Field(setting1=1)
    assert not f.required


def test_field_set_name():
    f = Field()
    f.set_name('test')
    assert f._name == 'test'


def test_field_get_settings_validator():
    f = Field()
    f._validate_my_setting = mock.Mock()
    assert f._get_setting_validator('my_setting') == f._validate_my_setting


def test_field_get_settings_validator_raise_configration_error():
    f = Field()
    f.set_name('test')
    nose.tools.assert_raises(
        FieldSet.ConfigurationError,
        f._get_setting_validator,
        'my_setting'
    )


def test_field_validate():
    f = Field(my_setting=1)
    f.set_name('test')

    f._validate_field = mock.Mock()
    f._validate_my_setting = mock.Mock()

    f.validate('value')

    f._validate_field.assert_called_with('value')
    f._validate_my_setting.assert_called_with('my_setting', 1, 'value')


def test_field_validate_raises_on_field_validation():
    f = Field(my_setting=1)
    f.set_name('test')

    f._validate_field = mock.Mock(side_effect=FieldSet.Error())
    f._validate_my_setting = mock.Mock()

    nose.tools.assert_raises(
        FieldSet.Error,
        f.validate,
        'value'
    )
    assert not f._validate_my_setting.called


def test_field_validate_raises_on_setting_validation():
    f = Field(my_setting=1)
    f.set_name('test')

    f._validate_field = mock.Mock()
    f._validate_my_setting = mock.Mock(side_effect=FieldSet.Error())

    nose.tools.assert_raises(
        FieldSet.Error,
        f.validate,
        'value'
    )
    f._validate_field.assert_called_with('value')

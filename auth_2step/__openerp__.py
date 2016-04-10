{
    "name" : "2 Step to login",
    "version" : "1.0",
    "description":"""
        After login, system will sent opt key to email of user. User will input it to access to system.
        """,
    "category" : "security",

    "depends" : [
                    'web', 'base_setup',
        'email_template',
                ],
    "author" : "lehoangan1988@gmail.com",
    "init_xml" : [],
    "update_xml" : [
            "views/email_template.xml",
            "views/user_view.xml",
        ],
    'qweb': ['static/src/xml/2step_login.xml'],
    'js': [
        'static/src/js/2step_login.js',
    ],
    "installable" : True,
    "active" : True,
}

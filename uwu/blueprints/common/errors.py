from flask import Blueprint, render_template ,abort

def register_error_handlers(app):

    @app.errorhandler(404)
    def page_not_found(error):
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        return render_template('500.html'), 500
    
    @app.route('/500')
    def error500():
        abort(500)








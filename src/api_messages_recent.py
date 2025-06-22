    @app.route('/api/messages/recent', methods=['GET'])
    def get_recent_messages():
        """Buscar mensagens recentes para overlay"""
        try:
            limit = request.args.get('limit', 10, type=int)
            limit = min(limit, 50)  # Máximo 50 mensagens
            
            # Buscar mensagens mais recentes
            messages = Message.query.order_by(Message.created_at.desc()).limit(limit).all()
            
            # Converter para dict e inverter ordem (mais antigas primeiro)
            messages_data = [msg.to_dict() for msg in reversed(messages)]
            
            return jsonify({
                'success': True,
                'messages': messages_data,
                'count': len(messages_data)
            })
            
        except Exception as e:
            print(f"❌ Erro ao buscar mensagens recentes: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500


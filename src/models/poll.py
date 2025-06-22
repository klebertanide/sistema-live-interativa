# Modelo de Enquetes
class Poll(db.Model):
    __tablename__ = 'polls'
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(500), nullable=False)
    option_a = db.Column(db.String(200), nullable=False)
    option_b = db.Column(db.String(200), nullable=False)
    votes_a = db.Column(db.Integer, default=0)
    votes_b = db.Column(db.Integer, default=0)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        total_votes = self.votes_a + self.votes_b
        return {
            'id': self.id,
            'question': self.question,
            'option_a': self.option_a,
            'option_b': self.option_b,
            'votes_a': self.votes_a,
            'votes_b': self.votes_b,
            'total_votes': total_votes,
            'percentage_a': round((self.votes_a / total_votes * 100) if total_votes > 0 else 0, 1),
            'percentage_b': round((self.votes_b / total_votes * 100) if total_votes > 0 else 0, 1),
            'active': self.active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


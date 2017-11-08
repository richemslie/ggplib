package propnet_convert;

import org.ggp.base.util.gdl.grammar.Gdl;
import org.ggp.base.util.statemachine.Move;
import org.ggp.base.util.statemachine.Role;

///////////////////////////////////////////////////////////////////////////////

public class MetaProposition extends MetaComponent {
    Gdl gdl;

    boolean is_base;
    boolean is_input;
    boolean is_legal;
    boolean is_goal;
    boolean is_init;
    boolean is_terminal;

    int goal_value;
    Move the_move;

    // for is_goal / is_legal... role is needed... (not sure what the lifetime for this is)
    Role role;
    int role_index;

    public MetaProposition() {
        this.is_base = false;
        this.is_input = false;
        this.is_legal = false;
        this.is_goal = false;
        this.is_init = false;
        this.is_terminal = false;
        this.goal_value = -1;
        this.the_move = null;
        this.role_index = -1;
    }

    public String toPython() {
        String t = "other";
        if (this.is_base) {
            t = "base";
        }

        if (this.is_input) {
            t = "input";
        }

        if (this.is_legal) {
            t = "legal";
        }

        if (this.is_goal) {
            t = "goal";
        }

        if (this.is_init) {
            t = "init";
        }

        if (this.is_terminal) {
            t = "terminal";
        }

        return String.format("(%d, %s, %s, %s, %s, %s, '%s')",
                             this.component_id, -1, this.type,
                             this.toPythonList(this.inputs),
                             this.toPythonList(this.outputs),
                             t,
                             this.gdl);
    }

}

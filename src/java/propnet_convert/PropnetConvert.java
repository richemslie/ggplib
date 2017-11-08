package propnet_convert;

import java.util.Map;
import java.util.Set;
import java.util.List;
import java.util.HashMap;

import org.ggp.base.util.game.Game;

import org.ggp.base.util.gdl.grammar.Gdl;
import org.ggp.base.util.gdl.grammar.GdlConstant;
import org.ggp.base.util.gdl.grammar.GdlRelation;
import org.ggp.base.util.gdl.grammar.GdlSentence;
import org.ggp.base.util.propnet.architecture.PropNet;
import org.ggp.base.util.propnet.architecture.Component;
import org.ggp.base.util.propnet.architecture.components.And;
import org.ggp.base.util.propnet.architecture.components.Or;
import org.ggp.base.util.propnet.architecture.components.Not;
import org.ggp.base.util.propnet.architecture.components.Constant;
import org.ggp.base.util.propnet.architecture.components.Transition;
import org.ggp.base.util.propnet.architecture.components.Proposition;
import org.ggp.base.util.propnet.factory.OptimizingPropNetFactory;
import org.ggp.base.util.statemachine.Move;
import org.ggp.base.util.statemachine.Role;


public class PropnetConvert {

    // The player roles
    public List<Role> roles;

    // internally we use role indexes
    public int role_count;

    // slow map of our meta components... only used at compile time
    public Map <Integer, MetaComponent> metas_map;

    public void translate(Game game) {

        List<Gdl> description = game.getRules();

        if (description == null || description.size() == 0) {
            throw new RuntimeException("Problem reading the file " + game + " or parsing the GDL.");
        }

        // we temporarily create another state machine to get us going
        PropNet opnf_propnet = null;
        try {
            // The ggp-base OPNF proposition network
            opnf_propnet = OptimizingPropNetFactory.create(description);

            System.out.println("Done OptimizingPropNetFactory.create()");
            //System.out.println(opnf_propnet.getInfo());

            OptimizingPropNetFactory.removeInits(opnf_propnet);

            // redos recording
            opnf_propnet = new PropNet(opnf_propnet.getRoles(), opnf_propnet.getComponents());

        } catch (InterruptedException e) {
            throw new RuntimeException(e.toString());
        }

        // set the roles
        this.roles = opnf_propnet.getRoles();
        this.role_count = this.roles.size();

        HashMap<Component, Integer> component_ids = new HashMap<Component, Integer>();
        int component_id = 0;
        for (Component c : opnf_propnet.getComponents()) {
            component_ids.put(c, component_id++);
        }

        // start by creating all the meta components
        this.metas_map = new HashMap <Integer, MetaComponent>();

        // create a map of component to component_ids

        // create the meta components
        for (Component c : opnf_propnet.getComponents()) {
            MetaComponent meta = null;

            if (c instanceof Proposition) {
                Proposition p = (Proposition) c;

                // create a meta proposition
                MetaProposition metap = new MetaProposition();
                meta = metap;

                metap.component_id = component_ids.get(c);
                metap.type = MetaComponent.PROPOSITION;

                // XXX getName() is worst named method ever...  Not my problem...
                metap.gdl = p.getName();

                // is it a base?
                metap.is_base = opnf_propnet.getBasePropositions().values().contains(c);

                // is it a input?
                metap.is_input = opnf_propnet.getInputPropositions().values().contains(c);

                // is it a legal?
                for (Map.Entry<Role, Set <Proposition>> entry : opnf_propnet.getLegalPropositions().entrySet()) {
                    if (entry.getValue().contains(c)) {

                        // only if we have the role
                        // some broken gdl games will generate some random goals for non-roles
                        if (this.roles.contains(entry.getKey())) {
                            metap.is_legal = true;
                            metap.role = entry.getKey();
                            metap.role_index = this.roleToIndex(entry.getKey());
                            break;
                        }
                    }
                }

                // is it a goal?
                for (Map.Entry<Role, Set <Proposition>> entry : opnf_propnet.getGoalPropositions().entrySet()) {

                    if (entry.getValue().contains(c)) {

                        // only if we have the role
                        // some broken gdl games will generate some random goals for non-roles
                        if (this.roles.contains(entry.getKey())) {
                            metap.is_goal = true;
                            metap.role = entry.getKey();
                            metap.role_index = this.roleToIndex(entry.getKey());
                            break;
                        }
                    }
                }

                // is it a init?
                if (c == opnf_propnet.getInitProposition()) {
                    metap.is_init = true;
                }

                // is it a terminal?
                if (c == opnf_propnet.getTerminalProposition()) {
                    metap.is_terminal = true;
                }

                if (metap.is_goal) {
                    GdlRelation relation = (GdlRelation) metap.gdl;
                    GdlConstant constant = (GdlConstant) relation.get(1);
                    metap.goal_value = Integer.parseInt(constant.toString());
                }

                if (metap.is_legal) {
                    GdlSentence sentence = (GdlSentence) metap.gdl;
                    metap.the_move = new Move(sentence.get(1));
                }

                if (metap.is_input) {
                    GdlSentence sentence = (GdlSentence) metap.gdl;
                    metap.the_move = new Move(sentence.get(1));
                }

            } else {
                meta = new MetaComponent();
                meta.component_id = component_ids.get(c);

                // need to decide what it is...
                if (c instanceof Or) {
                    meta.type = MetaComponent.OR;
                }

                if (c instanceof And) {
                    meta.type = MetaComponent.AND;
                }

                if (c instanceof Not) {
                    meta.type = MetaComponent.NOT;
                }

                if (c instanceof Transition) {
                    meta.type = MetaComponent.TRANSITION;
                }

                if (c instanceof Constant) {
                    Constant a_constant = (Constant) c;
                    meta.type = MetaComponent.CONSTANT;
                    meta.initial_value = a_constant.getValue();
                }
            }

            // finally add it for next pass
            this.metas_map.put(meta.component_id, meta);
        }

        // we need inputs/outputs in MetaComponent
        for (Component c : opnf_propnet.getComponents()) {
            for (Component o : c.getOutputs()) {
                MetaComponent m = this.metas_map.get(component_ids.get(c));
                m.outputs.add(this.metas_map.get(component_ids.get(o)));
            }
        }

        for (Component c : opnf_propnet.getComponents()) {
            for (Component i : c.getInputs()) {
                MetaComponent m = this.metas_map.get(component_ids.get(c));
                m.inputs.add(this.metas_map.get(component_ids.get(i)));
            }
        }
    }

    // helper:
    public int roleToIndex(Role the_role) {
        // set the role index
        int role_index = 0;
        for (Role r : this.roles) {
            if (r.equals(the_role)) {
                break;
            }

            role_index++;
        }

        return role_index;
    }

}

package propnet_convert;

import java.util.List;
import java.util.ArrayList;

public class MetaComponent {
    final static String PROPOSITION = "PROPOSITION";
    final static String OR = "OR";
    final static String AND = "AND";
    final static String NOT = "NOT";
    final static String TRANSITION = "TRANSITION";
    final static String CONSTANT = "CONSTANT";
    final static String UNKNOWN = "UNKNOWN";

    public String type;

    public int component_id;
    public boolean initial_value;

    public List <MetaComponent> inputs;
    public List <MetaComponent> outputs;


    MetaComponent() {
        this.inputs = new ArrayList <MetaComponent>();
        this.outputs = new ArrayList <MetaComponent>();

        this.type = MetaComponent.UNKNOWN;
    }

    protected String toPythonList(List <MetaComponent> lcomps) {
        int s = lcomps.size();
        StringBuilder sb = new StringBuilder();
        sb.append("[");
        int count = 0;
        for (MetaComponent c : lcomps) {
            count++;
            if (count < s) {
                sb.append(String.format("%s, ", c.component_id));
            } else {
                sb.append(String.format("%s", c.component_id));
            }
        }

        assert (count == s);
        sb.append("]");
        return sb.toString();
    }

    public String toPython() {
        String count = "-1";
        if (this.type == "CONSTANT") {
            if (this.initial_value) {
                count = "1";
            } else {
                count = "0";
            }
        }

        return String.format("(%d, %s, %s, %s, %s)",
                             this.component_id, count, this.type,
                             this.toPythonList(this.inputs),
                             this.toPythonList(this.outputs));
    }

}


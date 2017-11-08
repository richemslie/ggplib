package propnet_convert;

import java.io.File;
import java.io.IOException;
import java.io.PrintWriter;
import java.io.FileNotFoundException;

import java.util.Map;

import java.nio.file.Files;
import java.nio.file.Paths;

import org.ggp.base.util.game.Game;
import org.ggp.base.util.statemachine.Role;

public final class Convert {

    public static void main(String[] args) {
        String in_filename = args[0];
        String out_filename = args[1];
        PropnetConvert propnet_convert = new PropnetConvert();

        System.out.println("Building statemachine for " + in_filename);

        try {
            String infile_contents = new String(Files.readAllBytes(Paths.get(in_filename)));
            Game game = Game.createEphemeralGame(Game.preprocessRulesheet(infile_contents));
            propnet_convert.translate(game);
        } catch (IOException e) {
            System.out.println("Failed to translate to propnet: ");
            e.printStackTrace();
            throw new RuntimeException();
        }

        // write to file
        try {
            File out_file = new File(out_filename);
            PrintWriter writer = new PrintWriter(out_file);
            writer.println("# dumping propnet for " + in_filename);
            writer.println("# number of roles " + propnet_convert.role_count);
            writer.println("");
            writer.println("from ggplib.propnet.constants import *");
            writer.println("");

            writer.println("roles = [");
            for (Role role : propnet_convert.roles) {
                writer.println("    '" + role + "',");
            }

            writer.println("]");
            writer.println("");

            writer.println("entries = (");

            for (Map.Entry <Integer, MetaComponent> entry : propnet_convert.metas_map.entrySet()) {
                writer.println("    " + entry.getValue().toPython() + ",");
            }

            writer.println(")");
            writer.println("");
            writer.println("# DONE");

            writer.close();

        } catch (FileNotFoundException e) {
            System.out.println("FileNotFoundException: ");
            e.printStackTrace();
            throw new RuntimeException();
        }
    }
}

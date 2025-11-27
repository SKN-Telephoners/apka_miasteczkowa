import { createStackNavigator } from "@react-navigation/stack";
import EventScreen from "../screens/home/EventScreen";
import EventDetails from "../screens/home/EventDetails";
import AddEvent from "../screens/home/AddEvent";

const Stack = createStackNavigator();

const EventStack = () => {
  return (
    <Stack.Navigator>
      <Stack.Screen name="EventScreen" component={EventScreen} options={{ headerShown: false }} />
      <Stack.Screen name="EventDetails" component={EventDetails} options={{ title: "Szczegóły Wydarzenia" }} />
      <Stack.Screen name="AddEvent" component={AddEvent} options={{title: "Dodaj wydarzenie"}} />
    </Stack.Navigator>
  );
};

export default EventStack;

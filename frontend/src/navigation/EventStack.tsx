import { createStackNavigator } from "@react-navigation/stack";
import EventScreen from "../screens/home/EventScreen";
import EventDetails from "../screens/event/EventDetails";
import AddEvent from "../screens/event/AddEvent";
import EditEvent from "../screens/event/EditEvent";

const Stack = createStackNavigator();

const EventStack = () => {
  return (
    <Stack.Navigator>
      <Stack.Screen name="EventScreen" component={EventScreen} options={{ headerShown: false }} />
      <Stack.Screen name="EventDetails" component={EventDetails} options={{ title: "Szczegóły Wydarzenia" }} />
      <Stack.Screen name="AddEvent" component={AddEvent} options={{title: "Dodaj wydarzenie"}} />
      <Stack.Screen name="EditEvent" component={EditEvent} options={{title: "Edytuj wydarzenie"}} />
    </Stack.Navigator>
  );
};

export default EventStack;

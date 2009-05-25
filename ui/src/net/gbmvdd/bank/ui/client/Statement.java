package net.gbmvdd.bank.ui.client;

import com.google.gwt.core.client.JavaScriptObject;

public class Statement extends JavaScriptObject {
	protected Statement() {
	}
	
	public final native String getEventId() /*-{
		return this.event_id;
	}-*/;

	public final native String getBeginDate() /*-{
		return this.beginDate;
	}-*/;

	public final native String getEndDate() /*-{
		return this.endDate;
	}-*/;
}

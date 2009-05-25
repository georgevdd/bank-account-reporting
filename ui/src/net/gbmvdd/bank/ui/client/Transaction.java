package net.gbmvdd.bank.ui.client;

import com.google.gwt.core.client.JavaScriptObject;

public class Transaction extends JavaScriptObject {
	protected Transaction() {
	}
	
	public final native String getEventId() /*-{
		return this.event_id;
	}-*/;

	public final native String getFitId() /*-{
		return this.fitid;
	}-*/;

	public final native String getDate() /*-{
		return this.date;
	}-*/;
	
	public final native String getName() /*-{
		return this.name;
	}-*/;

	public final native String getMemo() /*-{
		return this.memo;
	}-*/;

	public final native String getAmount() /*-{
		return this.amount;
	}-*/;
}
